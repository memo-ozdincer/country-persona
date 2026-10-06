"""Separate native thinking tokens from public answers without promoting unfinished reasoning."""


def split_native_output(ids, *, thinking, open_id, close_id, eos_id):
    if len({open_id, close_id, eos_id}) != 3:
        raise ValueError('Distinct native marker IDs required')
    ids = list(ids)
    closes = [i for i, token in enumerate(ids) if token == close_id]
    malformed = open_id in ids or len(closes) > 1 or (not thinking and bool(closes))
    if malformed:
        return {'protocol_status': 'malformed_markers', 'reasoning_ids': ids, 'public_ids': [], 'boundary_tokens': 0}
    if thinking and not closes:
        return {'protocol_status': 'no_public_boundary', 'reasoning_ids': ids, 'public_ids': [], 'boundary_tokens': 0}
    boundary = closes[0] if thinking else -1
    return {'protocol_status': 'public_answer', 'reasoning_ids': ids[:boundary] if thinking else [],
            'public_ids': ids[boundary + 1:] if thinking else ids, 'boundary_tokens': int(thinking)}
