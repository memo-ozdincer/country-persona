"""Extract an exact span for the capacity in which Yamazaki made the Panel statement."""
import argparse
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

import institutional_candidate_fields as archived
from minurso_atomic_review import digest, pick, read_model

ROOT = archived.ROOT
AUDIT = ROOT / "benchmark-kit/validity-audit"
sys.path.insert(0, str(AUDIT))
import duplicate_card_atomic as atom
sys.path.pop(0)

SPANS = re.compile(
    r"\b(?:speaking (?:as|in) [^,.;]+|spoke (?:(?:solely )?in|as) [^,.;]+"
    r"|Council President Yamazaki|resumed the presidency|Yamazaki\b)"
)
SYSTEM = (
    "Select the exact excerpt that expressly states the capacity in which Yamazaki made his "
    "assessment of the veto's consequence for the Panel of Experts. The excerpt need not use the "
    "word capacity. A person's office or a later resumption of an office does not by itself "
    "identify the capacity of the statement. Ignore excerpts about another speaker or agenda item. "
    "Choose 'No explicit capacity' if the passage supplies none. Use only the candidate and reply with one letter."
)


def cases():
    for _, field, variant, passage, truth in atom.entries():
        if field == 1:
            yield f"source/{variant}", passage, {"full": 1, "reordered": 1, "missing": 0, "reversed": 2}[variant]
    for name, passage, field, truth in archived.cases():
        if field == "speaker-capacity":
            yield f"record/{name.rsplit('/', 1)[-1]}", passage, {1: 1, 2: 2, 0: 0}[truth]
    absent = next(passage for name, passage, _ in cases_base() if name == "source/missing")
    yield "scope/other-speaker", absent + " Another delegate spoke in his national capacity as Japan’s representative.", 0
    yield "scope/other-item", absent + (
        " Under a different agenda item, Yamazaki spoke in his national capacity as Japan’s representative."
    ), 0


def cases_base():
    for _, field, variant, passage, _ in atom.entries():
        if field == 1:
            yield f"source/{variant}", passage, {"full": 1, "reordered": 1, "missing": 0, "reversed": 2}[variant]


def spans(text):
    return [None, *[(m.start(), m.end(), m.group()) for m in SPANS.finditer(text)]]


def meaning(value):
    if value is None:
        return 0
    excerpt = value[2]
    if not excerpt.startswith(("speaking ", "spoke ")):
        return None
    if "Japan" in excerpt:
        return 1
    if "Council President" in excerpt:
        return 2
    return None


def observations():
    for name, passage, _ in cases():
        items = spans(passage)
        count = len(items)
        assert 1 < count <= 8
        for rotation in range(count):
            order = list(range(rotation, count)) + list(range(rotation))
            payload = {"candidate": passage, "choices": {
                letter: items[i][2] if i else "No explicit capacity"
                for letter, i in zip("ABCDEFGH"[:count], order, strict=True)}}
            yield {"observation": (name, rotation), "legal": order, "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def hashes():
    files = [Path(__file__).resolve(), Path(archived.__file__), Path(atom.__file__),
             atom.SEMANTIC_LOCK, archived.DPRK, archived.DPRK_KEY, archived.MALI, archived.MALI_KEY,
             ROOT / "relay_text.py"]
    return {str(p.relative_to(ROOT)): digest(p) for p in files}


def run(model, directory):
    sys.path.insert(0, str(ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


def report(directory):
    rows = read_model(directory, hashes(), observations())
    report_rows = []
    for name, passage, truth in cases():
        items = spans(passage)
        picked = [pick(rows[name, i]) for i in range(len(items))]
        selected = [items[i] if i is not None else None for i in picked]
        assert all(v is None or passage[v[0]:v[1]] == v[2] for v in selected)
        agreement = picked[0] if None not in picked and len(set(picked)) == 1 else None
        role = meaning(items[agreement]) if agreement is not None else None
        possible = {meaning(v) for v in items} - {0, None}
        heuristic = next(iter(possible)) if len(possible) == 1 else 0
        report_rows.append({"case": name, "truth": truth, "span_ids": picked, "exact_spans": selected,
                            "agreed_role": role, "span_heuristic_role": heuristic})
    return {"scope": "DPRK development excerpts, one archived model record and authored distractors. "
                     "A bounded phrase matcher proposes verbatim spans and decodes their role. "
                     "An exact substring can still have the wrong speaker or scope.",
            "actions_sha256": digest(directory / "actions.jsonl"), "rows": report_rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None:
            cli.error("run requires --model")
        run(args.model, args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
