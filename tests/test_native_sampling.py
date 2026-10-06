import torch
from country_persona.native_sampling import GeneratedPresencePenalty


def test_prompt_only_tokens_are_not_penalized():
    scores = torch.zeros(1, 8)
    processor = GeneratedPresencePenalty(3, 1.5)
    assert torch.equal(processor(torch.tensor([[1, 2, 3]]), scores), scores)
    result = processor(torch.tensor([[1, 2, 3, 4]]), scores)
    assert result[0, 1] == 0 and result[0, 4] == -1.5


def test_repeated_generated_tokens_receive_presence_not_frequency_penalty():
    processor = GeneratedPresencePenalty(1, 1.5); scores = torch.zeros(1, 8)
    result = processor(torch.tensor([[0, 4, 4, 4, 5]]), scores)
    assert result[0, 4] == result[0, 5] == -1.5 and result[0, 6] == 0


def test_presence_masks_are_independent_per_sequence_and_do_not_mutate_scores():
    processor = GeneratedPresencePenalty(1, 1.5); scores = torch.zeros(2, 8)
    result = processor(torch.tensor([[0, 4], [0, 5]]), scores)
    assert result[0, 4] == result[1, 5] == -1.5 and result[0, 5] == result[1, 4] == 0
    assert torch.equal(scores, torch.zeros_like(scores))
