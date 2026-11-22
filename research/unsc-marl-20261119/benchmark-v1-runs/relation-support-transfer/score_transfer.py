"""Read label-order effects and verify the canonical composed records."""
import json

from review_transfer import HERE, HUMAN, REPORT, RUNS, cards, load, prior, probes, read

report = read(REPORT / "source-preserving-transfer/scores.json")["outcomes"]["sponsors-first"]
human = read(HUMAN / "anchors.json")["literal"]
report_anchor = read(REPORT / "anchor.json")
judge = load("canonical_judge", RUNS.parent / "benchmark-v1.5/judge_score.py")
RECORDS = {
    "2739": (report["record"].removesuffix(" " + report["comparison"]), 56, 14, 130),
    "2664": (human["packet"]["answer"], 58, 12, 150),
}


def decision(probe, results):
    mapped = {}
    for key, labels in prior.LABELS.items():
        result = results[f"{probe['id']}/{key}"]
        support = next(k for k in labels if labels[k] == "supported")
        reject = next(k for k in labels if labels[k] == "unsupported")
        mapped[key] = result["logits"][support] - result["logits"][reject]
    mean = sum(mapped.values()) / len(mapped)
    return {"docket": probe["docket"], "supported": probe["supported"], "margins": mapped, "mean_margin": mean,
            "ab": mapped["ab"] > 0, "ba": mapped["ba"] > 0, "mean": mean > 0,
            "agreement": all(v > 0 for v in mapped.values())}


def measure(rows, method):
    positive = sum(r["supported"] for r in rows)
    negative = len(rows) - positive
    admitted_good = sum(r["supported"] and r[method] for r in rows)
    admitted_bad = sum(not r["supported"] and r[method] for r in rows)
    return {"supported_admitted": admitted_good, "supported": positive,
            "unsupported_admitted": admitted_bad, "unsupported": negative,
            "correct_decisions": admitted_good + negative - admitted_bad}


def supported_record(probe, assessment):
    docket = probe["docket"]
    required = {"sponsors", "algeria"} if docket == "2739" else {"safeguards", "india"}
    evidence = cards(docket)
    exact = {key: evidence[key] for key in required}
    candidate = probe["claim"]

    def bind(receipts, text):
        return receipts == exact and text == candidate

    assert set(probe["cards"]) == required and bind(exact, candidate)
    for key in exact:
        assert not bind({k: v for k, v in exact.items() if k != key}, candidate)
        assert not bind(exact | {key: exact[key] + " Altered."}, candidate)
        assert not bind(exact | {f"{key}-foreign": exact[key]}, candidate)
    assert not bind(exact, candidate + " Extra words.")
    baseline, score, bonus, cap = RECORDS[docket]
    def render(receipts, text, enabled):
        return baseline + " " + text if enabled and bind(receipts, text) else baseline

    final = render(exact, candidate, True)
    assert render(exact, candidate, False) == baseline
    assert render({}, candidate, True) == baseline
    assert len(final.split()) <= cap
    anchor = human if docket == "2664" else report_anchor
    packet = anchor["packet"] | {"answer": final}
    units = anchor["verdict"]["units"]
    relation = "relation" if docket == "2664" else "bounded-overlap"
    ready = []
    for mark in units:
        if mark["id"] == relation:
            ready.append({"id": relation, "status": "met", "response": candidate,
                          "source": [{"block": key, "quote": exact[key]} for key in sorted(exact)],
                          "reason": "The bounded comparison is supported by both supplied sources."})
        elif docket == "2739" and mark["id"] == "algeria-reason":
            # The fixed text uses the earlier independently reviewed extract.
            lead = "Algeria valued monthly reporting"
            assert lead in baseline
            ready.append(mark | {"response": baseline[baseline.index(lead):]})
        else:
            ready.append(mark)
    graded = judge.score(packet, anchor["verdict"] | {"units": ready})
    assert graded["strict"] and graded["final"]["lower"] == score + bonus == 70
    methods = {"standalone": False, "exact_source": True,
               **{method: assessment[method] for method in ("ab", "ba", "mean", "agreement")}}
    released_records = {method: render(exact, candidate, enabled) for method, enabled in methods.items()}
    release = {method: score + bonus * (record == final) for method, record in released_records.items()}
    public = 42 if docket == "2739" else 30
    p = 0.75
    utility = {method: public + p**2 * (value - score) - 4 for method, value in release.items()}
    return {"fixed_record": baseline, "candidate": candidate, "canonical_record": final,
            "required_source_ids": sorted(required), "release": release,
            "send_both_utility_at_75pct": utility, "withhold_utility": public}


def run():
    results = read(HERE / "verified.json")["outputs"]
    rows = probes()
    all_results = {r["id"]: decision(r, results) for r in rows}
    assert len(results) == len(rows) * 2
    transfer = {}
    for target, source in (("2739", "2664"), ("2664", "2739")):
        cut = max(0, *(r["mean_margin"] for r in all_results.values()
                       if r["docket"] == source and not r["supported"]))
        held = [r | {"transferred": r["mean_margin"] > cut}
                for r in all_results.values() if r["docket"] == target]
        transfer[target] = {"calibration_docket": source, "threshold": cut,
                            "outcome": measure(held, "transferred")}
    deployment = {r["docket"]: supported_record(r, all_results[r["id"]])
                  for r in rows if r.get("canonical")}
    summary = {
        name: {method: measure([r for r in all_results.values() if name == "all" or r["docket"] == name], method)
               for method in ("ab", "ba", "mean", "agreement")}
        for name in ("all", "2739", "2664")
    }
    return {"cases": all_results, "summary": summary, "transferred_cutoffs": transfer, "deployment": deployment}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
