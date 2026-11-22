"""Admit typed historical facts from exact source spans and compose a workshop record."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cyprus-transfer"))
import check as cyprus
import transfer as cy


OLD = cy.OLD
e, w = cyprus.e, cy.common
RUN = HERE / "evidence"
ARMS = ("mali", "cyprus", "cyprus-withheld")


def load(arm):
    if arm == "mali":
        world = w.roster()["pivotal"]
        case, menu, *_ = w.load()
        reader = [json.loads(line) for line in (OLD / "evidence" / "episodes.jsonl").read_text().splitlines()]
        episode = next(row for row in reader if row["id"] == "pivotal/learned")
        assert tuple(episode["world"]) == world
        state = tuple(episode["state"])
        rubric = e.read(w.MALI / "live" / "rubric.json")
        evidence = w.evidence(case, state)
        return case, menu, state, world, rubric, evidence
    case, menu, *_ = cy.setup()
    writer = next(x for x in cyprus.rows("trace.jsonl") if x["stage"] == "writer")
    state = tuple(writer["state"])
    public = [row for row in cy.public(case, state) if arm != "cyprus-withheld" or row["id"] != "vote"]
    return case, menu, state, cy.selected(), case["rubric"], public


def fields(arm):
    return e.read(HERE / "contracts.json")[arm.split("-")[0]]


def sources(arm):
    return {row["id"]: row["text"] for row in load(arm)[-1] if row.get("source") or row.get("url")}


def request(arm):
    return {"max_output_tokens": 480, "messages": [
        {"role": "system", "content": "Return one JSON object only. Each requested field maps to one exact contiguous quotation "
         "copied from the named evidence block. Use null if a source or field is missing. Do not paraphrase."},
        {"role": "user", "content": json.dumps({"fields": [
            {key: field[key] for key in ("id", "source", "description")} for field in fields(arm)],
            "evidence": sources(arm)}, ensure_ascii=False)},
    ]}


def direct(arm):
    sources_by_id = sources(arm)
    result = {}
    for field in fields(arm):
        text = sources_by_id.get(field["source"], "")
        found = re.search(field["pattern"], text)
        result[field["id"]] = found[0] if found else None
    return result


def admit(arm, proposed):
    admitted = {}
    status = {}
    originals = sources(arm)
    for field in fields(arm):
        key = field["id"]
        source = originals.get(field["source"])
        candidate = proposed.get(key)
        if source is None:
            status[key] = "missing_source"
        elif candidate is None:
            status[key] = "no_candidate"
        elif not isinstance(candidate, str) or candidate not in source:
            status[key] = "not_exact_for_source"
        else:
            matches = list(re.finditer(field["pattern"], candidate))
            if len(matches) != 1:
                status[key] = "field_coverage_missing"
            else:
                status[key] = "admitted"
                content = {"date": "30 August 2023"} | matches[0].groupdict()
                admitted[key] = field["render"].format(**content)
    return admitted, status


def compose(arm, proposed):
    case, menu, state, world, rubric, evidence = load(arm)
    admitted, status = admit(arm, proposed)
    decision = w.game.terminal(menu, state)[0]
    workshop = "Fictional briefing. " + w.renderer.public_conditions(case, state) + " " + cy.proof(case, state)
    if arm == "mali":
        workshop += " This workshop creates no authority over sanctions or expert mandates."
    else:
        workshop += " This workshop changes neither the Council resolution, the mandate nor the parties' positions."
    text = f"Decision: {decision}\n\n{workshop}"
    if admitted:
        text += "\n\n" + " ".join(admitted.values())
    packet_case = {"id": f"verified-record/{arm}", "track": "workshop",
                   "word_cap": 225 if arm == "mali" else 150, "gold": [w.game.terminal(menu, world)[0]],
                   "rubric": rubric, "task": "Write the historical record and the separate fictional workshop decision.",
                   "public": evidence + [{"id": "checked-exclusions", "text": cy.proof(case, state)}], "owned": []}
    return packet_case, {"text": text, "termination": "complete"}, status


def parse(reply):
    if reply["termination"] == "complete":
        try:
            answer = json.loads(reply["text"])
        except json.JSONDecodeError:
            return {}
        if isinstance(answer, dict):
            return answer
    return {}


def pins():
    files = (Path(__file__), HERE / "protocol.md", HERE / "contracts.json", HERE / "requests.json",
             OLD / "evidence" / "complete.json", cy.RUN / "complete.json", cy.HERE / "case.json",
             w.MALI / "case.json", w.MALI / "live" / "rubric.json")
    return {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in files}


def collect(generate, path):
    requests = {arm: request(arm) for arm in ARMS}
    assert requests == e.read(HERE / "requests.json")
    for arm, req in requests.items():
        w.archived.base.suite.append(path / "calls.jsonl", {"arm": arm, "request": req, "reply": generate(req)})
    (path / "inputs.json").write_text(json.dumps(pins(), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("requests", "direct", "run"))
    mode = parser.parse_args().mode
    if mode == "requests":
        e.emit({arm: request(arm) for arm in ARMS})
    elif mode == "direct":
        e.emit({arm: compose(arm, direct(arm))[1:] for arm in ARMS})
    else:
        with patch.object(w.archived.base.suite, "collect", collect), patch.object(
                w.archived.base, "roster", return_value=dict.fromkeys(ARMS)):
            w.archived.base.run(RUN)
