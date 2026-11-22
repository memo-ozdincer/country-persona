"""Retry source-owner recovery by selecting an exact span instead of transcribing it."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

import minurso_requery as requery

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "judge"))
from minurso_atomic_review import pick, read_model
sys.path.pop(0)

ORDERS = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
SYSTEM = (
    "Select the exact span that answers the requested field. A related phrase that states a different issue, "
    "or leaves out the event connection the question asks about, is insufficient. Use the supplied source only. "
    "Do not recite the quote. Answer with a single letter."
)
CANDIDATES = {
    "Monitoring": ("cited the report documenting the ninth consecutive year without an OHCHR visit",
                   "argued that MINURSO should have a human-rights monitoring component, as other missions do",
                   None),
    "Penholder": ("the penholder had disregarded Algeria's views",
                  None,
                  "explained Algeria's deliberate non-participation on the final resolution and said "
                  "the penholder had disregarded Algeria's views"),
}


def observations():
    sources = requery.base.case()["delegate_evidence"]["Algeria"]
    for field, (block, _, question) in requery.FIELDS.items():
        spans = CANDIDATES[field]
        assert all(span is None or span in sources[block] for span in spans)
        if field == "Penholder":
            question += " Select a span that connects the complaint with the specific participation decision."
        for index, order in enumerate(ORDERS):
            opts = [spans[k] or "No span explicitly answers." for k in order]
            body = {"source": sources[block], "question": question,
                    "choices": dict(zip("ABC", opts, strict=True))}
            yield {"observation": (field, index), "legal": order, "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
            ]}


def hashes():
    deps = (Path(__file__), Path(requery.__file__), requery.base.PACK, ROOT / "relay_text.py")
    return {str(p.resolve().relative_to(ROOT)): requery.digest(p) for p in deps}


def run(model, directory):
    sys.path.insert(0, str(ROOT))
    import relay_text
    with patch.multiple(relay_text, observations=observations, hashes=hashes):
        relay_text.score(model, directory)


def report(directory):
    rows = read_model(directory, hashes(), observations())
    found, decisions = {}, {}
    for field in CANDIDATES:
        votes = [pick(rows[field, k]) for k in range(len(ORDERS))]
        decisions[field] = votes
        choice = CANDIDATES[field][votes[0]] if None not in votes and len(set(votes)) == 1 else None
        if choice is not None:
            found[field] = choice
    source = requery.historical_sources()
    delivery = "\n".join(f"{field}: {found.get(field, 'MISSING')}" for field in requery.FIELDS)
    proof = requery.verify_quotes(delivery, source)
    results = {}
    for request, _ in requery.requests():
        if not request["id"].startswith("named-"):
            continue
        drafts = json.loads(request["messages"][1]["content"])["national_drafts"]
        text, met, _, guard = requery.render(request, drafts)
        role = []
        for field, rubric, claim in (
            ("Monitoring", "monitoring-position", "Algeria argued for a human-rights monitoring component in MINURSO"),
            ("Penholder", "penholder", "Algeria said the penholder disregarded its views, explaining its non-participation"),
        ):
            if field in proof:
                sentence = claim + " [DZ-DRAFT]."
                role.append(sentence)
                item = proof[field]
                met[rubric] = [sentence, [item["block"]], ["selected-source-reply", item["quote"]]]
        lines = text.splitlines()
        if role:
            lines[2] = "Algeria: " + " ".join(role)
        output = "\n".join(lines)
        seen = ["selected-source-reply", request["seen"][1]]
        compiled = {**request, "output": output, "ended": True, "seen": seen,
                    "input_ids": [], "output_ids": []}
        evaluated = requery.grade_final(compiled, {"met": met, "guard": guard},
                                        dict(zip(seen, (delivery, drafts["CH-DRAFT"]), strict=True)), [])
        results[request["id"]] = {"record": output, "grade": evaluated}
    return {"scope": "Closed evidence-selection retry. Menus are authored on this docket. "
                     "The same source-owner reply serves both arms, and public wording is fixed. "
                     "There are no new peer turns.",
            "actions_sha256": requery.digest(directory / "actions.jsonl"),
            "menu_decisions": decisions, "projected_delivery": delivery, "licensed_quotes": proof,
            "records": results}


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
