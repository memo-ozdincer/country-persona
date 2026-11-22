"""Score the Somalia record and evaluate equal-information routing under both budgets."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import somalia_transfer as t
import delivery_runtime as dispatch

w, route, n, e = t.LIB, t.router, t.n, t.e
a, o = route.a, route.o
here = t.HERE
PUBLIC = {"adoption": "vote", "transition": "mandate", "phase": "mandate",
          "end": "mandate", "reports": "mandate"}
COMPLETE = {"china": {"9"}, "somalia": {"8", "5"}, "us": {"7", "3"}}
LABEL = {"china": "China", "somalia": "Somalia", "us": "United States"}
LEADS = ("The United States ", "China ", "Somalia ", "It ")
INTERACTIONS = {
    "local-procurement": ({"china": {"2"}, "somalia": {"5"}}, "China and Somalia both urged local procurement."),
    "different-emphases": ({"china": {"9"}, "us": {"7", "3"}}, "China emphasized Somali ownership. The US objected to reduced reporting."),
}


def normalize(row, menus):
    with patch.object(w, "MENUS", menus), patch.object(route.s.q.t, "choose_ids", w_alias(menus)):
        original = w.selection(row["part"], row["response"])
        return route.s.q.normalize_ranked(row, original)


def w_alias(menus):
    def choose(row):
        return w.selection(row["part"], row["response"])
    return choose


def render(case, spans, selected, mask):
    candidates = [(role, label, len(ids) - i) for bit, (role, ids) in zip(n.BITS[1:], selected.items(), strict=True)
                  if mask & bit for i, label in enumerate(ids)]
    best = None
    for subset in product((False, True), repeat=len(candidates)):
        chosen = {role: set() for role in case["roles"]}
        weight = sum(rank for add, (_, _, rank) in zip(subset, candidates) if add)
        for add, (role, label, _) in zip(subset, candidates):
            if add:
                chosen[role].add(label)
        paragraphs = {}
        for role, ids in chosen.items():
            if not ids:
                continue
            clauses = []
            for span in sorted((spans[role][i] for i in ids), key=lambda x: x["start"]):
                text = span["text"]
                for lead in LEADS:
                    if text.startswith(lead):
                        text = text[len(lead):]
                        break
                clauses.append(text[0].upper() + text[1:])
            paragraphs[role] = LABEL[role] + ": " + " ".join(clauses)
        comparisons = {key: s for key, (required, s) in INTERACTIONS.items()
                       if all(values <= chosen[role] for role, values in required.items())}
        text = "\n\n".join([case["public_text"], *paragraphs.values(), *comparisons.values()])
        words = len(text.split())
        if words > case["word_cap"]:
            continue
        objective = (sum(COMPLETE[key] <= ids for key, ids in chosen.items()),
                     len(comparisons), len(paragraphs), weight, words)
        if best is None or objective > best[0]:
            best = objective, {"text": text, "local": paragraphs, "comparison": comparisons,
                               "used": {key: sorted(ids) for key, ids in chosen.items()}, "words": words}
    assert best is not None
    return best[1]


def grade():
    case = n.read(t.SOURCE)
    spans = t.plan()["spans"]
    raw = {row["part"]: normalize(row, case["menus"]) for row in t.calls()}
    native = {role: ids for role, (ids, _) in raw.items()}
    control = {role: list(ids) for role, ids in case["menus"].items()}
    sources = {row["id"]: row["text"] for row in case["public"]}
    rows = {}
    for key, selection in (("native", native), ("menu_order", control)):
        records = {}
        for mask in range(8):
            output = render(case, spans, selection, mask)
            selected = {role: set(ids) for role, ids in output["used"].items()}
            assert all(not selected[role] or mask & bit for role, bit in zip(case["roles"], n.BITS[1:]))
            calls = [{}, {}, {"text": output["text"], "termination": "complete"}]
            packet = e.final_packet(case, calls)

            def mark(criterion, evidence, text, present):
                return {"id": criterion, "status": "met" if present else "unmet",
                        "response": text if present else "",
                        "source": [{"block": source, "quote": sources[source]} for source in evidence] if present else [],
                        "reason": "The designated statements preserve the full criterion." if present else
                                  "At least one supporting statement is missing."}

            entries = [mark(k, [v], case["public_text"], True) for k, v in PUBLIC.items()]
            entries.extend(mark(f"{role}-position", [role], output["local"].get(role, ""), need <= selected[role])
                           for role, need in COMPLETE.items())
            for criterion, (present, _) in INTERACTIONS.items():
                pair = list(present)
                text = output["text"] if criterion in output["comparison"] else ""
                entries.append(mark(criterion, pair, text, bool(text)))
            verdict = {"id": packet["id"], "units": entries,
                       "guard": {"status": "clear", "source": [], "response": "",
                                 "reason": "Speaker attribution, conditional authority and the reporting reservation are scoped."}}
            record = e.final_score(case, calls, verdict)
            records[mask] = {"output": output, "packet": packet, "marks": verdict, "score": record}
        rows[key] = records
    return {"selection": raw, "records": rows}


def five(calibration, grade):
    base = calibration[0]
    design = np.array([base + sum(calibration[bit] - base for bit in (1, 2, 4) if mask & bit)
                       for mask in range(8)])
    design[[3, 7]] += grade - design[3]
    return np.clip(design, 0, 70)


def replay(graded):
    opening_params = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    bank_table = {tag: np.array([rows[str(k)]["score"]["released_70"] for k in range(8)], dtype=float)
                  for tag, rows in graded["records"].items()}
    result, examples = [], {}
    for endpoint, bank in bank_table.items():
        calibration = {k: bank[k] for k in range(7) if k != 3}
        forecast = five(calibration, bank[3])
        for prior_name, (actual, dominant) in a.laws().items():
            for info, prior in (("correct_mixture", actual), ("dominant_only", dominant)):
                baseline = forecast.copy()
                for mask in (3, 5, 6, 7):
                    baseline[mask] = min(70., bank[0] + sum(bank[b] - bank[0] for b in (1, 2, 4) if mask & b))
                opening = o.replan.study.opening(baseline, prior, opening_params)
                mass, held = o.opening(*opening, prior), o.opening(*opening, actual)
                controls = o.controls(bank, held, actual, opening)
                strongest = max(r["net"] for k, r in controls.items() if k != "exact_ask_reply")
                for budget, grader in ((5, five), (7, route.forecasts)):
                    cache = {}
                    for offset in (-7, 0, 7):
                        with patch.object(route, "forecasts", grader):
                            choices = route.evaluate_locked(calibration, bank[3] + offset, prior, opening, mass, cache)
                        row = {}
                        for policy, (key, actions) in choices.items():
                            score = o.measure(bank, held, actual, opening, actions)
                            assert score["net"] <= controls["exact_ask_reply"]["net"] + 1e-10
                            row[policy] = {"selected": (key[0] - 1, key[1]), "net_over_oracle_fixed": score["net"] - strongest,
                                           "quality_over_silence": score["released"] - controls["exact_no_request"]["released"]}
                        if endpoint == "native" and budget == 7 and offset == 0 and prior_name not in examples:
                            predicted, witness = dispatch.trace_table(actual, opening, {k: v[1] for k, v in choices.items()}, bank)
                            for method, trace in predicted.items():
                                assert abs(trace["net"] - strongest - row[method]["net_over_oracle_fixed"]) < 1e-10
                            if witness:
                                for method in witness["routes"].values():
                                    method["record"] = graded["records"]["native"][str(method["receipt"])]["output"]["text"]
                                examples[prior_name] = witness
                        result.append({"endpoint": endpoint, "budget": budget, "prior": prior_name,
                                       "suite": endpoint, "prior_information": info, "review_offset": offset, "routes": row})
    summary = {f"{k}/{b}": route.summarize([r for r in result if r["endpoint"] == k and r["budget"] == b])
               for k in bank_table for b in (5, 7)}
    hashes = (Path(__file__), here / "assessment.md", here / "grades.json", Path(route.__file__))
    return {"score_banks": {k: r.tolist() for k, r in bank_table.items()}, "rows": result, "summary": summary,
            "dispatcher_witnesses": examples, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in hashes}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("grades", "replay"))
    e.emit(grade() if cli.parse_args().mode == "grades" else replay(n.read(here / "grades.json")))
