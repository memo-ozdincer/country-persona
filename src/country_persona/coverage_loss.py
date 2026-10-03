"""Frozen clause allocation for response-only causal loss; no extra target text.

The base allocation retains 25% uniform token mass. The other 75% is shared
equally by annotated national-fact/application sentences. Each example retains
its original total supervised-token mass, including EOS and boundary prose.
"""
import math
import re


def annotate_target(text):
    paragraphs = text.split('\n\n')
    if len(paragraphs) != 3 or not paragraphs[0].startswith('Documented position: ') or not paragraphs[1].startswith('Recommendation: ') or not paragraphs[2].startswith('Commitment boundary: '):
        raise ValueError('Unexpected target contract')
    spans = []
    for paragraph, prefix, kind in zip(paragraphs[:2], ('Documented position: ', 'Recommendation: '), ('national_fact', 'application')):
        start = text.index(paragraph) + len(prefix)
        body = paragraph[len(prefix):]
        boundaries = [0] + [m.end() for m in re.finditer(r'(?<=[.!?])\s+(?=[A-Z])', body)] + [len(body)]
        for a, b in zip(boundaries, boundaries[1:]):
            while a < b and body[a].isspace():
                a += 1
            while b > a and body[b-1].isspace():
                b -= 1
            if b > a:
                spans.append({'start': start+a, 'end': start+b, 'text': body[a:b], 'kind': kind})
    return spans


def token_allocation(offsets, prefix_tokens, content_start, spans, bonus_fraction=0.75):
    if not 0 <= bonus_fraction < 1 or not 0 < prefix_tokens < len(offsets) or not spans:
        raise ValueError('Invalid completion boundary/allocation')
    occupied = set()
    clauses = []
    for span in spans:
        a, b = content_start+span['start'], content_start+span['end']
        indices = [i for i, (x, y) in enumerate(offsets) if i >= prefix_tokens and x < b and y > a]
        if not indices or set(indices) & occupied:
            raise ValueError('Empty or overlapping token clause')
        occupied.update(indices)
        clauses.append(indices)
    n = len(offsets)-prefix_tokens
    weights = [0.0]*prefix_tokens + [1.0-bonus_fraction]*n
    for indices in clauses:
        addition = bonus_fraction*n/(len(clauses)*len(indices))
        for i in indices:
            weights[i] += addition
    if not math.isclose(sum(weights), n, abs_tol=1e-8):
        raise ValueError('Per-example token mass changed')
    return weights, clauses


class FrozenCoverageLoss:
    """TRL custom loss keyed by exact supervised target IDs, never decoded text."""
    def __init__(self, records, uniform=False):
        self.targets = {}
        self.calls = 0
        self.denominators = []
        for record in records:
            key = tuple(record['target_ids'])
            weights = [1.0]*len(key) if uniform else record['target_weights']
            if len(key) != len(weights) or not key or any(not math.isfinite(w) or w <= 0 for w in weights):
                raise ValueError('Invalid frozen weights')
            if not math.isclose(sum(weights), len(key), abs_tol=1e-7):
                raise ValueError('Loss mass must match original target tokens')
            if key in self.targets and self.targets[key] != weights:
                raise ValueError('Same target has conflicting allocations')
            self.targets[key] = weights

    def weights_for(self, labels):
        import torch
        weights = torch.zeros(labels.shape, dtype=torch.float32, device=labels.device)
        for i, row in enumerate(labels):
            valid = row != -100
            key = tuple(row[valid].detach().cpu().tolist())
            if key not in self.targets:
                raise ValueError('Unfrozen or truncated supervised target')
            weights[i, valid] = torch.tensor(self.targets[key], device=labels.device)
        return weights

    def __call__(self, outputs, labels, num_items_in_batch=None):
        import torch
        from torch.nn import functional as F
        weights = self.weights_for(labels)[:, 1:]
        shifted = labels[:, 1:]
        logits = outputs.logits[:, :-1, :].float()
        token_loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), shifted.reshape(-1), ignore_index=-100, reduction='none').reshape(shifted.shape)
        denominator = (shifted != -100).sum() if num_items_in_batch is None else num_items_in_batch
        denominator = torch.as_tensor(denominator, device=logits.device)
        if int(denominator) < int((shifted != -100).sum()) or int(denominator) <= 0:
            raise ValueError('Invalid accumulation denominator')
        self.calls += 1
        self.denominators.append(int(denominator))
        return (token_loss*weights).sum()/denominator


class FrozenChunkedCoverageLoss(FrozenCoverageLoss):
    """Same chunk projection/order/metrics as pinned TRL; weighted token NLL.

    Used through the existing chunked forward. It does not request full logits
    or change the backbone, adapters, labels or generation path.
    """
    def __call__(self, hidden_states, lm_head_weight, chunk_size, labels=None,
                 shift_labels=None, num_items_in_batch=None, logit_scale=1.0,
                 final_logit_softcapping=None, lm_head_bias=None):
        import torch
        from torch.nn import functional as F
        from torch.utils.checkpoint import checkpoint
        from trl.trainer.sft_trainer import maybe_gather_lm_head_ctx
        if labels is None or shift_labels is not None:
            raise ValueError('Only frozen single-GPU unshifted-label protocol is supported')
        weights = self.weights_for(labels)[:,1:].reshape(-1)
        hidden = hidden_states[:,:-1,:].reshape(-1,hidden_states.shape[-1])
        target = labels[:,1:].reshape(-1)
        valid = target != -100
        n_valid = valid.sum()
        order = valid.to(torch.int8).argsort(descending=True,stable=True)
        hidden,target,weights = hidden[order],target[order],weights[order]
        n_padded = (n_valid/chunk_size).ceil().clamp(min=1).to(torch.int64)*chunk_size

        def chunk(h,w,b,lbl,scale,cap,token_weights):
            with maybe_gather_lm_head_ctx(w,b):
                logits = (h@w.to(h.dtype).t()).float()
                if b is not None:
                    logits = logits+b.float()
            if scale != 1.0:
                logits = logits*scale
            if cap is not None:
                logits = cap*torch.tanh(logits/cap)
            log_p = F.log_softmax(logits,dim=-1)
            per_token = F.nll_loss(log_p,lbl,ignore_index=-100,reduction='none')
            mask = lbl != -100
            return (per_token*token_weights).sum(),((logits.argmax(-1)==lbl)&mask).sum().float(),(-(log_p.exp()*log_p).sum(-1)*mask).sum()

        loss = hidden.new_zeros((),dtype=torch.float32)
        correct = loss.clone()
        entropy = loss.clone()
        for start in range(0,n_padded,chunk_size):
            part = slice(start,start+chunk_size)
            value,accuracy,information = checkpoint(chunk,hidden[part],lm_head_weight,lm_head_bias,target[part],logit_scale,final_logit_softcapping,weights[part],use_reentrant=False)
            loss,correct,entropy = loss+value,correct+accuracy,entropy+information
        denominator = n_valid if num_items_in_batch is None else num_items_in_batch
        denominator = torch.as_tensor(denominator,device=loss.device)
        if int(denominator) < int(n_valid) or int(denominator)<=0:
            raise ValueError('Invalid accumulation denominator')
        self.calls += 1
        self.denominators.append(int(denominator))
        return loss/denominator,correct,entropy,n_valid
