"""Author-profile sampling with generated-text-only presence semantics."""
import math
import time
from .io import digest


class GeneratedPresencePenalty:
    """Subtract a fixed logit penalty once per distinct generated token, excluding prompt."""
    def __init__(self, prompt_length, penalty):
        if prompt_length < 1 or not math.isfinite(penalty): raise ValueError('Invalid presence configuration')
        self.prompt_length = prompt_length; self.penalty = penalty; self.calls = 0

    def __call__(self, input_ids, scores):
        import torch
        self.calls += 1
        generated = input_ids[:, self.prompt_length:]
        if generated.shape[1] == 0: return scores
        seen = torch.zeros_like(scores, dtype=torch.bool)
        seen.scatter_(1, generated, True)
        return scores - seen.to(scores.dtype) * self.penalty


def generate_sampled_controls(model, tokenizer, rows, metadata, config):
    import torch
    from transformers import GenerationConfig, LogitsProcessorList
    model.eval(); settings = config['sampling_profile']
    generation = GenerationConfig(do_sample=True, max_new_tokens=config['generation_max_new_tokens'], use_cache=True,
                  pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id,
                  **{k: settings[k] for k in ('temperature', 'top_p', 'top_k', 'min_p', 'repetition_penalty')})
    result = []
    for row, meta in zip(rows, metadata):
        ids = tokenizer.apply_chat_template(row['prompt'], tokenize=True, return_dict=False, add_generation_prompt=True, **config['chat_template_kwargs'])
        if len(ids) + generation.max_new_tokens > config['max_length']: raise ValueError('No truncation allowed')
        penalty = GeneratedPresencePenalty(len(ids), settings['presence_penalty'])
        tensors = torch.tensor([ids], device='cuda:0')
        # Reset after all base/PEFT loading; loader RNG use cannot alter the paired sampling seed.
        torch.manual_seed(config['seed']); started = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(input_ids=tensors, attention_mask=torch.ones_like(tensors),
                         generation_config=generation, logits_processor=LogitsProcessorList([penalty]))
        torch.cuda.synchronize(); output = generated[0, len(ids):].tolist()
        assert penalty.calls == len(output)
        result.append({'id': meta['id'], 'country': meta['country_iso3'], 'input_ids': ids, 'input_ids_digest': digest(ids),
                       'output_ids': output, 'output': tokenizer.decode(output, skip_special_tokens=True), 'generated_tokens': len(output),
                       'generation_seconds': time.perf_counter() - started, 'at_output_cap': len(output) == generation.max_new_tokens,
                       'effective_generation_config': generation.to_dict(), 'presence_processor_calls': penalty.calls,
                       'presence_penalty': penalty.penalty, 'presence_scope': 'distinct generated tokens only, including reasoning; excludes prompt; not a frequency penalty',
                       'sampling_seed_reset_before_generation': config['seed'], 'scope': 'source-policy development'})
    return result
