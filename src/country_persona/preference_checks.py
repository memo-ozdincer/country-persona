"""Exact input/target and prompt/padding checks for the bounded preference fit."""
from .io import digest


def validate_pair(original,pair,audit):
    if pair['prompt']!=original['prompt'] or pair['chosen']!=original['completion'] or digest(pair)!=audit['pair_sha256']:
        raise ValueError('Preferred target or prompt changed')
    chosen=pair['chosen'][0]['content']
    edit=audit['edit']
    if chosen[edit['start']:edit['end']]!=edit['before']:
        raise ValueError('Edit offset mismatch')
    if pair['rejected']!=[{'role':'assistant','content':chosen[:edit['start']]+edit['after']+chosen[edit['end']:]}]:
        raise ValueError('Rejected answer differs beyond declared edit')
    if not audit['chosen_ids'] or not audit['rejected_ids'] or audit['chosen_ids']==audit['rejected_ids']:
        raise ValueError('Missing or identical preference targets')


def audit_preference_masks(dataset,collator,audits):
    for row,a in zip(dataset,audits):
        for key in ('prompt_ids','chosen_ids','rejected_ids'):
            if row[key]!=a[key]:
                raise ValueError('Actual DPO tokenizer differs: '+key)
        batch=collator([row])
        for i,key in enumerate(('chosen_ids','rejected_ids')):
            ids=a['prompt_ids']+a[key]
            n=len(a['prompt_ids'])
            if batch['input_ids'][i,:len(ids)].tolist()!=ids or int(batch['attention_mask'][i].sum())!=len(ids):
                raise ValueError('Preference collator changed or truncated tokens')
            mask=batch['completion_mask'][i]
            if mask[:n].any() or not mask[n:len(ids)].all() or mask[len(ids):].any():
                raise ValueError('Prompt/padding included or target excluded from preference loss')
    return {'pairs':len(audits),'actual_trainer_token_ids_and_masks_checked':True,'prompt_and_padding_excluded':True,
        'chosen_tokens_once':sum(len(a['chosen_ids']) for a in audits),'rejected_tokens_once':sum(len(a['rejected_ids']) for a in audits),
        'sequence_tokens_once':sum(2*len(a['prompt_ids'])+len(a['chosen_ids'])+len(a['rejected_ids']) for a in audits)}


def use_torch_preference_logprobs():
    """Use pinned TRL's official fallback with FP32 softmax/reduction, locally."""
    import trl.trainer.utils as utils
    import trl.trainer.dpo_trainer as dpo
    utils._fused_logprob_entropy = None
    def logprobs(logits,index,**kwargs):
        return utils.selective_log_softmax(logits.float(),index,**kwargs)
    def logprobs_and_entropy(logits,index,**kwargs):
        return utils.selective_log_softmax_and_entropy(logits.float(),index,**kwargs)
    dpo.selective_log_softmax = logprobs
    dpo.selective_log_softmax_and_entropy = logprobs_and_entropy
    return 'Pinned TRL built-in PyTorch fallback with FP32 softmax/reductions; optional Triton disabled in this process only.'
