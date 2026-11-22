"""Recover comparisons from model-selected source spans and a constrained renderer."""
import argparse
from copy import deepcopy
from itertools import chain
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "delisting-comparison-writer"
sys.path.insert(0, str(PRIOR))
import collect_relation as baseline
import score as scoring

BUDGET = baseline.BUDGET
CONNECTIVES = {
    "authority": "The delegate described the adopted division of roles.",
    "review": "The delegate's preferred timing differs from the Council's stated intention.",
}
SYSTEM = (
    "Select evidence for an explicit comparison in a Council brief. "
    "Return exactly NONE unless one of these two relations is supported: "
    "authority means the delegate describes a reporting role with the committee deciding "
    "and the adopted document sets that same division, with no recommendation from the reporting body; "
    "review means the delegate prefers a fixed-time review and the adopted document expresses "
    "an intention for continuing review. A rejected, quoted, draft, or merely similar claim "
    "does not establish either relation. Read the whole source for each speaker's actual stance. "
    'If supported, return only JSON: {"type":"authority or review","delegate":["exact span"],'
    '"document":["exact span"]}. Select one or two brief contiguous substrings per source. '
    "For authority, show the report's purpose, its lack of recommendation, and who decides. "
    "For review, show the preference, the operative verb expressing intention, and continuous timing. "
    "Use the shortest exact spans that preserve those details. Across all spans use at most 27 words. "
    "Copy the words as they occur, without altering capitalization, spelling or punctuation."
)


def plan():
    old = baseline.read(PRIOR / "plan.json")
    spec = deepcopy(old)
    case = baseline.read(baseline.CASE / "case.json")
    controls = {
        name: (("malta/authority" if row["type"] == "authority" else "a3plus/review"),
               "delegate_statement" if row["side"] == "early" else "adopted_document", row["text"])
        for name, row in case["controls"].items()
    }
    for key, (matched, field, text) in controls.items():
        row = deepcopy(old["requests"][matched])
        row["id"] = f"control/{key}"
        sources = json.loads(row["messages"][1]["content"])
        sources[field] = text
        row["messages"][1]["content"] = json.dumps(sources, ensure_ascii=False)
        spec["requests"][row["id"]] = row
    for row in spec["requests"].values():
        row["messages"][0]["content"] = SYSTEM
    for path in (Path(__file__), HERE / "protocol.md", PRIOR / "plan.json", PRIOR / "score.py"):
        spec["pins"][str(path.relative_to(HERE.parents[1]))] = baseline.pin(path)
    return spec


def spans(reply, sources):
    if reply["termination"] != "complete":
        return None, reply["termination"]
    if reply["text"] == "NONE":
        return None, "abstained"
    try:
        obj = json.loads(reply["text"])
    except ValueError:
        return None, "invalid_json"
    if (not isinstance(obj, dict) or set(obj) != {"type", "delegate", "document"}
            or not isinstance(obj["type"], str) or obj["type"] not in CONNECTIVES):
        return None, "invalid_schema"
    for owner, field in (("delegate", "delegate_statement"), ("document", "adopted_document")):
        quotes = obj[owner]
        if not isinstance(quotes, list) or not 1 <= len(quotes) <= 2:
            return None, "invalid_span_count"
        if not all(isinstance(span, str) and span.strip() and span in sources[field] for span in quotes):
            return None, f"not_in_{owner}_source"
        if len(quotes) != len(set(quotes)):
            return None, "duplicate_span"
    if sum(len(quote.split()) for quote in chain(obj["delegate"], obj["document"])) > 27:
        return None, "quote_budget"
    return obj, None


def render(reply, sources):
    obj, failure = spans(reply, sources)
    if failure:
        return {"text": "NONE", "witnesses": None, "fallback": failure}
    join = lambda items: " … ".join(f"“{span}”" for span in items)
    text = f'{CONNECTIVES[obj["type"]]} Delegate: {join(obj["delegate"])}. Adopted text: {join(obj["document"])}.'
    if len(text.split()) > 40:
        return {"text": "NONE", "witnesses": obj, "fallback": "render_length"}
    return {"text": text, "witnesses": obj, "fallback": None}


def rendered(spec, outputs):
    return {key: render(reply, json.loads(spec["requests"][key]["messages"][1]["content"]))
            for key, reply in outputs.items()}


def main(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == baseline.read(HERE / "plan.json")
    if mode in {"render", "score"}:
        verified = baseline.read(HERE / "verified.json")
        renderings = rendered(spec, verified["outputs"])
        if mode == "render":
            return renderings
        actual = baseline.read(PRIOR / "plan.json")["requests"]
        projected = spec | {"requests": {key: spec["requests"][key] for key in actual}}
        outputs = {key: verified["outputs"][key] | {"text": renderings[key]["text"]} for key in actual}

        def read_for_score(path):
            if path == HERE / "plan.json":
                return projected
            if path == HERE / "verified.json":
                return verified | {"outputs": outputs}
            return baseline.read(path)

        with patch.object(scoring, "HERE", HERE), patch.object(scoring, "plan", return_value=projected), patch.object(
            scoring, "read", side_effect=read_for_score
        ):
            result = scoring.run()
        return result | {"renderings": renderings, "control_marks": baseline.read(HERE / "control-marks.json")}
    with patch.object(baseline.chair, "HERE", HERE), patch.object(
        baseline.chair, "OUT", HERE / "evidence"
    ), patch.object(baseline.chair, "BUDGET", BUDGET), patch.object(
        baseline.chair, "locked", return_value=spec
    ):
        return {"run": baseline.chair.run, "verify": baseline.chair.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "render", "score"))
    mode = parser.parse_args().mode
    result = main(mode)
    if mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
