"""Preserve source-exact national reasons in the fixed receipt comparison."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bound_writer as b
import bound_eval as score
import population

n = b.n
OUT = HERE / "evidence"
BASE_PLAN = b.plan
CHECK = {
    "Brazil": "Preserve mission support, whether the draft kept operational freedom, and the extent it addressed Lebanon's concerns.",
    "China": "Preserve mission support, the extent it addressed Lebanon's concerns, and what China emphasized about host authority or consent.",
    "Russia": "Preserve mission support, the late-drafting reason for abstention, and what happened to the earlier compromise.",
}


def plan():
    parent = n.read(HERE.parent / "plan.json")
    with patch.object(b, "HERE", HERE.parent):
        assert BASE_PLAN() == parent
    rows = parent["requests"]
    for row in rows:
        part = row["part"]
        if part == "public":
            system = ("Write one complete compact paragraph of at most 62 words from these two official blocks. "
                      "Use the exact draft symbol with its sponsor, meeting date, adopted resolution, "
                      "and three vote counts with the abstainers. Next state mandate expiry and that UNIFIL "
                      "acts without prior permission within its mandate and continues coordination with Lebanon's "
                      "Government under the status-of-forces agreement. Omit meeting ID, optional votes and commentary.")
        else:
            system = (
                "Return JSON only with keys excerpts, mission_support_quote, and host_concerns. "
                "Choose one or two exact contiguous excerpts in source order, totaling at most 25 words. "
                "Each excerpt must be a verbatim substring. Do not paraphrase or add ellipses. "
                + CHECK[part] +
                " For mission_support_quote copy an exact continuous phrase from one chosen excerpt that expresses mission support; "
                "use an empty string if none. For host_concerns return null or an object with assessment "
                "(some, insufficient or sufficient) and quote (an exact span from a chosen excerpt). "
                "Fill host_concerns only if a selected passage evaluates how much the text addresses the host's concerns."
            )
        row["request"]["messages"][0]["content"] = system
    paths = (Path(__file__), HERE / "protocol.md", HERE.parent / "plan.json",
             HERE.parent / "bound_eval.py", HERE.parent / "population.py")
    return {"requests": rows, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


plain_admit = b.admit
visibility_fixture = score.structure_check


def reject(issue):
    return {"summary": "", "mission_support_quote": "", "host_concerns": None, "issues": [issue]}


def admit(part, response, source):
    if part == "public":
        return plain_admit(part, response, source)
    if response["termination"] != "complete":
        return plain_admit(part, response, source)
    try:
        row = json.loads(response["text"])
    except json.JSONDecodeError:
        return reject("invalid_json")
    if not isinstance(row, dict) or set(row) != {"excerpts", "mission_support_quote", "host_concerns"}:
        return reject("non_extractive_schema")
    excerpts = row["excerpts"]
    cursor = 0
    valid = isinstance(excerpts, list) and len(excerpts) in (1, 2)
    for excerpt in excerpts if valid else ():
        start = source.find(excerpt, cursor) if isinstance(excerpt, str) and excerpt.strip() else -1
        if start < 0:
            valid = False
            break
        cursor = start + len(excerpt)
    if not valid or sum(len(line.split()) for line in excerpts) > 25:
        return reject("invalid_excerpts")
    rendered = " ".join("“" + line + "”" for line in excerpts)
    normalized = {"summary": f"{part} position: {rendered}",
                  "mission_support_quote": row["mission_support_quote"], "host_concerns": row["host_concerns"]}
    admitted = plain_admit(part, response | {"text": json.dumps(normalized)}, "\n".join(excerpts))
    # The supplied quote must occur in one excerpt and cannot cross the splice.
    for key in ("mission_support_quote", "host_concerns"):
        item = admitted[key]
        quote = item["quote"] if isinstance(item, dict) else item
        if quote and not any(quote in line for line in excerpts):
            admitted[key] = "" if key == "mission_support_quote" else None
            admitted["issues"].append(f"cross_excerpt_{key}")
    return admitted | {"excerpts": excerpts}


def structure_check():
    with patch.object(b, "admit", plain_admit):
        masks = visibility_fixture()
    old = {"summary": "Desk supports the mission.", "mission_support_quote": "", "host_concerns": None}
    new = {"excerpts": ["Desk supports the mission."],
           "mission_support_quote": "supports the mission", "host_concerns": None}
    source = "Desk supports the mission. It discussed coordination."

    def check(payload, evidence=source):
        return admit("Desk", {"text": json.dumps(payload), "termination": "complete"}, evidence)

    assert check(old)["issues"] == ["non_extractive_schema"]
    assert check(new)["excerpts"] == new["excerpts"]
    assert check(new, "Desk opposes the mission.")["issues"] == ["invalid_excerpts"]
    reversed_spans = {"excerpts": ["It discussed coordination.", "Desk supports the mission."]}
    assert check(new | reversed_spans)["issues"] == ["invalid_excerpts"]
    assert not check(new | {"mission_support_quote": "It discussed coordination."})["mission_support_quote"]
    return masks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "fragments", "packets", "verify", "score", "population"))
    mode = parser.parse_args().mode
    with patch.multiple(b, HERE=HERE, OUT=OUT, plan=plan, admit=admit), patch.object(
            score, "structure_check", structure_check):
        if mode == "run":
            with patch.object(n.base.suite, "collect", b.collect), patch.object(
                    n.base, "roster", return_value={"matched-unifil-extractive-writer": None}):
                n.base.run(OUT)
        else:
            actions = {"plan": plan, "verify": score.verify, "fragments": score.fragments,
                       "packets": lambda: score.packets()[1], "score": score.score, "population": population.run}
            n.matched.e.emit(actions[mode]())
