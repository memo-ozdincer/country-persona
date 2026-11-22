"""Build a finite canonical JSON language over a small role-local menu."""
from itertools import permutations
import json


def build(ids, encode, decode, eos):
    roles = tuple(ids)
    if len(roles) > 6 or not roles or any(type(i) is not str or not i for i in roles):
        raise ValueError("Expected a small nonempty string ID menu")
    root = {}
    paths = 0
    longest = 0
    for size in range(len(roles) + 1):
        for chosen in permutations(roles, size):
            text = json.dumps(list(chosen), ensure_ascii=False, separators=(",", ":"))
            tokens = tuple(encode(text))
            if not tokens or eos in tokens or decode(tokens) != text:
                raise ValueError("The tokenizer must preserve every valid message")
            node = root
            for token in (*tokens, eos):
                node = node.setdefault(token, {})
            paths += 1
            longest = max(longest, len(tokens) + 1)
    return root, paths, longest


def allowed(tree, continuation):
    node = tree
    for token in continuation:
        if token not in node:
            raise ValueError("Generated continuation left the allowed passage language")
        node = node[token]
    return list(node)


def validate(ids, text):
    try:
        selected = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid passage JSON") from exc
    if (not isinstance(selected, list) or not all(type(i) is str and i in ids for i in selected)
            or len(selected) != len(set(selected))
            or text != json.dumps(selected, ensure_ascii=False, separators=(",", ":"))):
        raise ValueError("The message violates canonical role-local passage JSON")
    return selected
