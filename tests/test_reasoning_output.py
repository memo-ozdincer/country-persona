from country_persona.reasoning_output import split_native_output


def parse(ids, thinking=True):
    return split_native_output(ids, thinking=thinking, open_id=101, close_id=102, eos_id=103)


def test_unfinished_reasoning_cannot_be_promoted_to_an_answer():
    result = parse([10, 11, 12])
    assert result['protocol_status'] == 'no_public_boundary'
    assert result['public_ids'] == [] and result['reasoning_ids'] == [10, 11, 12]


def test_native_boundary_separates_answer_and_preserves_all_tokens():
    ids = [10, 11, 102, 20, 21, 103]
    result = parse(ids)
    assert result['reasoning_ids'] == [10, 11] and result['public_ids'] == [20, 21, 103]
    assert len(result['reasoning_ids']) + result['boundary_tokens'] + len(result['public_ids']) == len(ids)


def test_disabled_thinking_has_no_generated_boundary():
    assert parse([20, 103], False)['public_ids'] == [20, 103]
    assert parse([102, 20, 103], False)['protocol_status'] == 'malformed_markers'


def test_reopened_or_multiple_reasoning_boundaries_cannot_certify_an_answer():
    assert parse([101, 10, 102, 20])['public_ids'] == []
    assert parse([10, 102, 20, 102, 30])['public_ids'] == []
