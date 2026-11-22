"""Apply the locked Myanmar criterion map and evaluate routing under each forecast."""
import argparse
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

import numpy as np

spec = spec_from_file_location("myanmar_record_transfer", Path(__file__).with_name("transfer.py"))
t = module_from_spec(spec)
spec.loader.exec_module(t)

e, n, m = t.e, t.n, t.m
PUBLIC = {
    "draft-act": ("vote", "The record names the adopted draft and resolution."),
    "vote-count": ("vote", "The record gives the full tally and the three abstainers."),
    "humanitarian": ("mandate", "The record names ending violence and humanitarian access."),
    "asean": ("mandate", "The record states ASEAN's central role and its reporting coordination with the UN."),
    "reporting": ("mandate", "The actor, oral mode, recipient, deadline and ASEAN coordination are given."),
    "authority": ("vote mandate", "The adopted instrument and its authority retain their historical status."),
}
REASONS = {
    "uk": "The roll call and national excerpt identify sponsorship, a yes vote and the rationale.",
    "india": "The roll call and national excerpt identify India's abstention and the diplomatic or regional rationale.",
    "role": "The procedural announcement is distinct from the later national explanation.",
}


def normalize_ranked(row, initial):
    if initial[1] == "admitted" or row["response"]["termination"] != "complete":
        return initial
    try:
        choices = json.loads(row["response"]["text"])
    except json.JSONDecodeError:
        return initial
    if not isinstance(choices, list) or not choices:
        return initial
    for rank, item in enumerate(choices, 1):
        if (not isinstance(item, dict) or set(item) != {"id", "importance"}
                or type(item["importance"]) is not int or item["importance"] != rank):
            return initial
    payload = row["response"] | {"text": json.dumps([item["id"] for item in choices])}
    ids, status = t.choose_ids(row | {"response": payload})
    return (ids, "normalized_ranked_ids") if status == "admitted" else initial


def grade():
    deck = t.plan()
    case = t.source_case()
    blocks = {r["id"]: r["text"] for r in case["public"]}
    raw = t.calls()
    trace = {row["part"]: t.choose_ids(row) for row in raw}
    normalized = {row["part"]: normalize_ranked(row, trace[row["part"]]) for row in raw}
    ordered = {role: ids for role, (ids, _) in trace.items()}
    rank_objects = {role: ids for role, (ids, _) in normalized.items()}
    plain = {role: list(card) for role, card in t.CARDS.items()}
    records = {}
    for tag, choice in (("native", ordered), ("rank_normalized", rank_objects), ("menu_order", plain)):
        cases = {}
        for mask in range(8):
            record = t.pack(mask, choice, deck)
            roles = {role: set(ids) for role, ids in record["used"].items()}
            header = record["text"].split("\n\n")[0]
            paragraphs = record["text"].split("\n\n")[1:]
            calls = [{}, {}, {"text": record["text"], "termination": "complete"}]
            packet = e.final_packet(case, calls)

            def item(key, meets, response, keys, reason):
                return {"id": key, "status": "met" if meets else "unmet",
                        "response": response if meets else "",
                        "source": [{"block": name, "quote": blocks[name]} for name in keys.split()] if meets else [],
                        "reason": reason if meets else "The complete item is absent."}

            entries = [item(key, True, header, keys, reason) for key, (keys, reason) in PUBLIC.items()]
            for key, role in (("uk", "uk"), ("india", "india"), ("role", "chair")):
                paragraph = next((p for p in paragraphs if p.startswith(t.LABELS[role] + " — ")), "")
                response = (header + "\n\n" + "\n\n".join(paragraphs[:paragraphs.index(paragraph) + 1])
                            if paragraph and role in ("uk", "india") else paragraph)
                entries.append(item(key, t.enough(role, roles[role]), response,
                                    "vote " + role if role in ("uk", "india") else role, REASONS[key]))
            entries.append(item("overlap", t.overlaps(roles), "\n\n".join(paragraphs), "vote uk india",
                                "Both national sources discuss regional concerns or consultation and the public vote differs."))
            marks = {"id": packet["id"], "units": entries,
                     "guard": {"status": "clear", "response": "", "source": [],
                               "reason": "Public authority and each attributed national explanation are kept distinct."}}
            score = e.final_score(case, calls, marks)
            cases[mask] = {"record": record, "packet": packet, "marks": marks, "score": score}
        records[tag] = cases
    return {"selected": trace, "posthoc_format_normalization": normalized, "pair": deck["calibration"], "records": records}


def evaluate(bank, prior, pair, parameters, original, review_delta=0):
    openings = m.o.replan.study.opening(t.cal.estimated(bank), prior, original)
    mass = m.o.opening(*openings, prior)
    controls = m.o.controls(bank, mass, prior, openings)
    exact_fixed = max((r["net"], key) for key, r in controls.items() if key != "exact_ask_reply")[1]
    quiet = controls["exact_no_request"]
    result = {}
    for key, enabled in (("singleton", 0), ("locked_pair", pair)):
        predicted = t.cal.estimated(bank, enabled)
        if enabled and review_delta:
            changed = np.bitwise_and(np.arange(8), enabled) == enabled
            predicted[changed] = np.clip(predicted[changed] + review_delta, 0, 70)
        oracle = m.o.exact_parts(mass, predicted)
        candidates = {"quiet": oracle["exact_no_request"]}
        for mode, fit in zip(("dense", "sparse"), parameters, strict=True):
            candidates[mode] = m.data.learned_maps(predicted, mass, fit, prior, openings, with_pruning=True)
        for card in range(1, 4):
            chair = np.where(m.D.CHAIR_LEGAL[:, card], card, 0)
            candidates[f"fixed_{card}"] = (chair, m.o.choose_response(chair, mass, predicted))
        forecast = {k: m.o.measure(predicted, mass, prior, openings, policy) for k, policy in candidates.items()}
        eligible = [k for k, r in forecast.items() if r["released"] >= forecast["quiet"]["released"] - 1e-10]
        best = max(eligible, key=lambda k: (forecast[k]["net"], k == "quiet"))
        candidates["exact_forecast"] = oracle["exact_ask_reply"]
        actual = {k: m.o.measure(bank, mass, prior, openings, arm) for k, arm in candidates.items()}
        assert all(r["net"] <= controls["exact_ask_reply"]["net"] + 1e-10 for r in actual.values())
        result[key] = {"prediction": predicted.tolist(), "selected": best, "forecast": forecast,
                       "held": actual, "selected_margin_vs_oracle_fixed": actual[best]["net"] - controls[exact_fixed]["net"],
                       "selected_released_delta_vs_silence": actual[best]["released"] - quiet["released"]}
    return {"exact_controls": controls, "best_oracle_fixed": exact_fixed, "approaches": result}


def replay(scored):
    parameters = tuple([np.array(a) for a in n.read(path)["parameters"]]
                       for path in (m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json"))
    original = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    prior_rows = m.o.R.TEST_PRIORS
    witness = n.read(n.WITNESS)["cases"]["myanmar"]["asymmetric"]["first"]
    setup = n.setup

    def matched():
        _, case, requests = setup()
        return witness, case, requests

    cases = {}
    for tag, rows in scored["records"].items():
        point = np.array([rows[str(mask)]["score"]["released_70"] for mask in range(8)], dtype=float)
        with patch.object(n, "setup", matched):
            triplet = n.comparison(point.tolist())
        cases[tag] = {"bank": point.tolist(), "matched": triplet,
                      "population": {key: evaluate(point, law, scored["pair"]["mask"], parameters, original)
                                     for key, law in prior_rows.items()}}
    return cases


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("grade", "replay"))
    e.emit(grade() if cli.parse_args().mode == "grade" else replay(json.loads((t.HERE / "grades.json").read_text())))
