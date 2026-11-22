"""Collect two tightly scoped native writer contrasts."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import witness as w
import review_witness as review


def deck():
    row = review.rows("episodes.jsonl")[0]
    assert row["id"] == "pivotal/learned" and row["certification"] == "IMPASSE"
    assert row["record"]["reply"]["termination"] == "cap"
    source = row["record"]["request"]
    payload = json.loads(source["messages"][-1]["content"])
    sources = {item["id"]: item for item in payload["evidence"]}
    menu = sources.pop("menu")
    delivered = sources.pop("delivered")
    scope = sources.pop("scope")
    task = (
        "Write at most 225 words. Begin with exactly Decision: A, Decision: B, Decision: C, Decision: D, "
        "Decision: IMPASSE, or Decision: UNRESOLVED. Compare the confirmed fictional requirements with "
        "all four menu options. If every option is incompatible, certify IMPASSE even if one requirement "
        "is unknown. If one or more options remain but any requirement is unknown, use UNRESOLVED. "
        "Certify a package only if all three requirements are confirmed and compatible. Immediately "
        "after the Decision line state the known role requirements and any remaining unknown. For an "
        "impasse name which requirement rules out each option. Then give a brief paragraph on both "
        "historical drafts, their sponsors, tallies, reasons for failure, positions and limits of authority. "
        "Preserve the distinction between the historical votes and the fictional workshop."
    )
    proof = {"task": task, "evidence": [menu, delivered, scope, *sources.values()]}
    return {
        "length_only": source | {"max_output_tokens": 420},
        "proof_first": {"messages": [source["messages"][0],
                        {"role": "user", "content": json.dumps(proof, ensure_ascii=False)}],
                        "max_output_tokens": 280},
    }


def collect(generate, path):
    requests = deck()
    assert requests == w.archived.E.read(HERE / "requests.json")
    for label, request in requests.items():
        w.archived.base.suite.append(path / "calls.jsonl", {
            "id": label, "request": request, "reply": generate(request)})
    files = (Path(__file__), HERE / "protocol.md", HERE / "requests.json",
             w.RUN / "complete.json", w.RUN / "episodes.jsonl")
    pins = {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in files}
    (path / "inputs.json").write_text(json.dumps(pins, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("deck", "run"))
    if parser.parse_args().mode == "deck":
        w.archived.E.emit(deck())
    else:
        with patch.object(w.archived.base.suite, "collect", collect), patch.object(w.archived.base, "roster", deck):
            w.archived.base.run(HERE / "evidence")
