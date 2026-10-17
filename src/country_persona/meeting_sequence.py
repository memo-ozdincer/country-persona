"""Source-bound chronological meeting continuations, independent of chat-role APIs."""
import hashlib
import re


MARKERS = ("<|scenario|>", "<|speaker|>", "<|speech|>")
COUNTRY_MARKERS = tuple(f"<|country_{c}|>" for c in ("FRA", "GBR", "IND", "BRA"))
NEW_TOKENS = MARKERS + COUNTRY_MARKERS
END = "<|im_end|>"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def validate(meeting, source):
    if digest(source) != meeting["source_sha256"]:
        raise ValueError("Source bytes changed")
    if not meeting["scenario"].strip():
        raise ValueError("Scenario required")
    if any(t in source or t in meeting["scenario"] for t in (*NEW_TOKENS, END)):
        raise ValueError("Reserved marker in source/scenario")
    previous_end = 0
    for turn in meeting["turns"]:
        start, end = turn["start"], turn["end"]
        if not previous_end <= start < end <= len(source):
            raise ValueError("Overlapping, unordered or invalid source spans")
        if previous_end and source[previous_end:start].strip():
            raise ValueError("Undeclared gap in chronological context")
        if not start <= turn.get("content_start", start) < end:
            raise ValueError("Invalid speech-content boundary")
        if turn["capacity"] not in {"national_delegation", "council_president", "record_event"}:
            raise ValueError("Unknown institutional capacity")
        if turn["phase"] not in {"before_vote", "vote_event", "after_vote"}:
            raise ValueError("Unknown meeting phase")
        if (turn["institution"] != "UNSC" or "\n" in turn["representative"]
                or not re.fullmatch(r"[A-Z]{3}|NONE", turn["country"])
                or any(t in turn["representative"] for t in (*NEW_TOKENS, END))):
            raise ValueError("Invalid speaker metadata")
        previous_end = end
    if not meeting["turns"] or source[previous_end:].strip():
        raise ValueError("Unsegmented trailing source")


def header(turn):
    country = turn["country"]
    label = f"<|country_{country}|>" if country in {"FRA", "GBR", "IND", "BRA"} else country
    return (f"<|speaker|>country={label}; institution={turn['institution']}; "
            f"capacity={turn['capacity']}; representative={turn['representative']}; "
            f"phase={turn['phase']}\n<|speech|>\n")


def render(meeting, source, target_index):
    validate(meeting, source)
    if not 0 <= target_index < len(meeting["turns"]):
        raise ValueError("Invalid target index")
    prefix = "<|scenario|>\n" + meeting["scenario"] + END + "\n"
    for turn in meeting["turns"][:target_index]:
        prefix += header(turn) + source[turn.get("content_start", turn["start"]):turn["end"]] + END + "\n"
    target = meeting["turns"][target_index]
    prefix += header(target)
    start = target.get("content_start", target["start"])
    body = source[start:target["end"]]
    return {"prefix": prefix, "body": body, "completion": body + END,
            "history_turns": target_index, "target_source_span": [start, target["end"]]}


def tokenize_example(tokenizer, rendered, max_length=8192):
    prefix = tokenizer.encode(rendered["prefix"], add_special_tokens=False)
    full = tokenizer.encode(rendered["prefix"] + rendered["completion"], add_special_tokens=False)
    if full[:len(prefix)] != prefix:
        raise ValueError("Tokenizer boundary is not prefix-stable; refuse incorrect loss masking")
    if len(full) > max_length:
        raise ValueError("Complete context exceeds budget; no silent truncation")
    if len(full) <= len(prefix):
        raise ValueError("No target tokens")
    return {"input_ids": full, "labels": [-100] * len(prefix) + full[len(prefix):],
            "prefix_tokens": len(prefix), "supervised_tokens": len(full) - len(prefix)}
