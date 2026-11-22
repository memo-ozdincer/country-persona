"""Collect source sentence pointers and matched semantic judgments."""
import argparse
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PRIOR = RUNS / "witnessed-documentary-routing"
OUT = HERE / "evidence"
sys.path.insert(0, str(PRIOR))
import collect_witnesses as old

engine = old.engine
collector = old.collector
SPLITS = re.compile(r"(?<!Mr\.)(?<!Ms\.)(?<!Dr\.)(?<=[.!?])\s+(?=[A-Z“])")
POINTER = re.compile(r"^S(\d+)(?:-S(\d+))?$")
SELECT = (
    "Select one complete sentence or a consecutive range of at most four sentences that explicitly "
    "establishes the precise claim. Include antecedents needed for the statement to stand on its own. "
    "The range must contain at most 100 words. Return an ID such as S3, a range such as S3-S5, "
    "or exactly NONE if the exact claim is not established. Return only the ID, range or NONE."
)
REQUIRED = {
    "reform": (
        "The statement must contain an objection by this speaker to insufficient time to negotiate the "
        "specified current draft. General comments about how much time negotiation should have, a future "
        "negotiation, or criticism alone without the timing objection do not qualify."
    ),
    "afghanistan": (
        "The span must state all three: appointment of the envoy, the speaker's own willingness to support "
        "the appointment, and agreement or assent from the de facto Afghan authorities as a condition for "
        "that support. Consultation or regard for their views does not entail assent, even if called a "
        "fundamental condition. An unidentified reference to a decision cannot establish the action."
    ),
}


def read(path):
    return json.loads(path.read_text())


def index_sentences(source):
    starts_and_ends = [(m.start(), m.end()) for m in SPLITS.finditer(source)]
    starts = [0, *(right for _, right in starts_and_ends)]
    stops = [*(left for left, _ in starts_and_ends), len(source)]
    return [{"id": f"S{i}", "start": left, "stop": right, "text": source[left:right]}
            for i, (left, right) in enumerate(zip(starts, stops, strict=True), 1) if right > left]


def plan():
    previous = old.locked()
    paths = (Path(__file__), HERE / "protocol.md", PRIOR / "collect_witnesses.py",
             PRIOR / "plan.json", PRIOR / "results.json")
    return {"pins": {**previous["pins"], **{
                str(p.relative_to(RUNS.parent)): collector.sha(p) for p in paths}},
            "checkpoint_index_sha256": previous["checkpoint_index_sha256"],
            "views": previous["views"], "hypotheses": previous["hypotheses"], "labels": previous["labels"],
            "selector": SELECT, "verifier": previous["verify"], "required": REQUIRED}


def locked():
    data = plan()
    assert data == read(HERE / "plan.json")
    return data


def resolve(response, indexed, source):
    if response["termination"] != "complete" or not (match := POINTER.fullmatch(response["text"])):
        return None
    first = int(match[1])
    last = int(match[2]) if match[2] else first
    if not 1 <= first <= last <= len(indexed) or last - first + 1 > 4:
        return None
    start, stop = indexed[first - 1]["start"], indexed[last - 1]["stop"]
    text = source[start:stop]
    if not 0 < len(text.split()) <= 100:
        return None
    return {"first": first, "last": last, "start": start, "stop": stop, "text": text}


def episode(call, spec):
    results = {}
    for name, row in spec["views"].items():
        family, source = row["family"], row["text"]
        claim = spec["hypotheses"][family]
        indexed = index_sentences(source)
        response = call(engine.earlier.request(f"{name}/select", 24, spec["selector"], {
            "claim": claim, "first_message": [{"id": entry["id"], "text": entry["text"]} for entry in indexed],
        }))
        span = resolve(response, indexed, source)
        verification = {}
        if span:
            for arm in ("prior", "necessary"):
                instruction = spec["verifier"] + (" " + spec["required"][family] if arm == "necessary" else "")
                verification[arm] = {}
                for order, labels in spec["labels"].items():
                    verification[arm][order] = call(engine.earlier.request(f"{name}/{arm}/{order}", 2, instruction, {
                        "first_message": span["text"], "claim": claim, "responses": labels,
                    }))
        results[name] = {"id_reply": response, "span": span, "verification": verification}
    return results


def act(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == read(HERE / "plan.json")
    run_model = collector.run

    def track(directory):
        with patch.object(collector, "roster", return_value={"2553-and-2721-indexed-witnesses": {}}):
            return run_model(directory)

    with patch.object(engine, "HERE", HERE), patch.object(engine, "OUT", OUT), patch.object(
        engine, "locked", return_value=spec
    ), patch.object(engine, "episode", episode), patch.object(collector, "run", side_effect=track):
        return {"run": engine.run, "verify": engine.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    result = act(mode)
    if mode != "run":
        print(json.dumps(result, indent=2, ensure_ascii=False))
