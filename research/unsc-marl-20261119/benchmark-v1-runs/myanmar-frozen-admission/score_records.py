"""Route admitted Myanmar claims into the unchanged historical rubric."""
import argparse
from itertools import product
from pathlib import Path
from statistics import mean
import sys

import transfer as run

HERE, e, CASE = run.HERE, run.e, run.CASE
sys.path.insert(0, str(run.FIT / "documentary-replay"))
from documentary import admissions, POLICIES

PUBLIC = ("On 21 December 2022, the Council adopted draft S/2022/980 as resolution 2669 (2022), 12–0–3. "
          "China, India and Russia abstained. The United Kingdom voted in favour.")
SHARED = "Both took regional perspectives into account. The United Kingdom supported adoption, while India abstained."
ASSERTIONS = {
    "uk-position": "The United Kingdom sponsored the draft and stressed ending violence and enabling aid after Council, ASEAN and regional consultations.",
    "india-position": "India advocated quiet, constructive diplomacy and cited neighbours’ concerns.",
    "chair-role": "India’s Council President announced adoption. India’s representative separately explained its national abstention.",
    "humanitarian-terms": "The resolution demands an immediate end to violence and calls for humanitarian access.",
    "oral-report": ("Recognizing ASEAN’s central role, the Council requested an oral report by 15 March 2023 to the Council "
                    "from the Secretary-General or his Special Envoy in coordination with the ASEAN Special Envoy, "
                    "on UN support for the Five-Point Consensus."),
}
CREDITS = {
    "uk-position": {"uk": ("vote", "uk")},
    "india-position": {"india": ("vote", "india")},
    "chair-role": {"role": ("chair",)},
    "humanitarian-terms": {"humanitarian": ("mandate",)},
    "oral-report": {"asean": ("mandate",), "reporting": ("mandate",)},
}
CORE = {
    "draft-act": (("vote",), "the Council adopted draft S/2022/980 as resolution 2669 (2022)"),
    "vote-count": (("vote",), "12–0–3. China, India and Russia abstained."),
    "authority": (("vote",), PUBLIC),
}


def lock():
    paths = (Path(__file__), HERE / "plan.json", HERE / "protocol.md",
             run.FIT / "documentary-replay/documentary.py", run.FIT / "fit.json",
             run.RELEASE / "release.json")
    return {"input_hashes": {str(path.relative_to(run.team.STUDY)): run.team.pin(path) for path in paths},
            "public": PUBLIC, "assertions": ASSERTIONS, "shared": SHARED}


def record(keys, mask, registry, labels):
    statements = {}
    for key in keys:
        row = registry[key]
        assert run.BLOCKS[row["source"]]["text"] == row["witness"]
        if mask & row["owner"]:
            statements[key] = ASSERTIONS.get(key, row["assertion"])
    rewarded = CORE.copy()
    for key, text in statements.items():
        for unit, blocks in CREDITS.get(key, {}).items():
            rewarded[unit] = blocks, text

    sections = [PUBLIC, *statements.values()]
    if {"uk-position", "india-position"} <= statements.keys():
        sections.append(SHARED)
        rewarded["overlap"] = ("uk", "india", "vote"), SHARED

    text = " ".join(sections)
    # The full national-position criteria also need the recorded votes in the public lead.
    for key in ("uk", "india"):
        if key in rewarded:
            blocks, span = rewarded[key]
            rewarded[key] = blocks, text[:text.index(span) + len(span)]
    calls = [{}, {}, {"text": text, "termination": "complete"}]
    violations = [key for key in statements if labels[key] != "supports"]
    guard = {"status": "clear", "source": [], "response": "",
             "reason": "The recorded disposition and admitted role statements are supported."}
    if violations:
        source = registry[violations[0]]["source"]
        guard = {"status": "failed", "source": [{"block": source, "quote": run.BLOCKS[source]["text"]}],
                 "response": statements[violations[0]], "reason": "The source does not support the published statement."}
    units = []
    for rule in CASE["rubric"]:
        name = rule["id"]
        blocks, span = rewarded.get(name, ((), ""))
        units.append({"id": name, "status": "met" if span else "unmet", "response": span,
                      "source": [{"block": k, "quote": run.BLOCKS[k]["text"]} for k in blocks],
                      "reason": rule["rule"] if span else "The received record omits required evidence."})
    verdict = {"id": e.final_packet(CASE, calls)["id"], "units": units, "guard": guard}
    return {"record": text, "admitted": list(statements), "false_assertions": violations,
            "verdict": verdict, "score": e.final_score(CASE, calls, verdict)}


def run_all():
    run.lock()
    assert lock() == e.read(HERE / "scoring-plan.json")
    notes = e.read(HERE / "plan.json")["fixtures"]
    registry = {row["id"]: {k: v for k, v in row.items() if k != "expected"} for row in notes}
    gold = {row["id"]: row["expected"] for row in notes}
    files = e.read(HERE / "verified.json")["evidence_sha256"]
    calls = run.OUT / "calls.jsonl"
    assert run.team.pin(calls) == files["calls.jsonl"]
    values = run.team.observations(calls, "held")
    assert set(registry) == set(values)
    frozen = e.read(run.FIT / "fit.json")["frozen"]
    rows, audit, summaries = {}, {}, {}
    for order in (0, 1):
        choices = {key: admissions(view, frozen, order) | {"privileged_semantic": gold[key]}
                   for key, view in values.items()}
        audit[str(order)] = choices
        for arm, mask in product(POLICIES, range(4)):
            keys = [key for key in registry if choices[key][arm] == "supports"]
            rows[f"{order}/{arm}/{mask}"] = record(keys, mask, registry, gold)
    assert len(rows) == 40
    for order in (0, 1):
        assert [rows[f"{order}/privileged_semantic/{mask}"]["score"]["released_70"] for mask in range(4)] == [21, 49, 35, 70]
    for arm in POLICIES:
        full = [rows[f"{order}/{arm}/3"]["score"]["released_70"] for order in (0, 1)]
        outcomes = [rows[f"{order}/{arm}/{mask}"]["score"] for order, mask in product((0, 1), range(4))]
        matches = [picked[arm] == gold[key] for order in audit.values() for key, picked in order.items()]
        wrong = [picked[arm] != gold[key] and picked[arm] != "unknown"
                 for order in audit.values() for key, picked in order.items()]
        summaries[arm] = {"full_receipt": full, "uniform_receipt_mean": mean(r["released_70"] for r in outcomes),
                          "guard_failures": sum(r["guard"] == "failed" for r in outcomes),
                          "relation_accuracy": sum(matches), "wrong_admissions": sum(wrong)}
    return {"summary": summaries, "admission_labels": audit, "records": rows,
            "scoring_plan_sha256": run.team.pin(HERE / "scoring-plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    e.emit({"plan": lock, "run": run_all}[parser.parse_args().mode]())
