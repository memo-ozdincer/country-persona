"""Separate composition losses from routing losses in the measured writer bank."""
import json
from itertools import permutations

import receipt_score as study

relay = study.relay
transfer = study.transfer


def compose(bank):
    spec = transfer.named_sources()[0]["unami"]
    public, cap = spec[3], spec[5]
    output = {}
    for ids in bank:
        units = [bank[frozenset({name})] for name in spec[0] if name in ids]
        text = "\n".join(row["supplement"] for row in units)
        full = public + "\n" + text
        optional = sum(row["optional_points"] for row in units)
        guard = all(row["guard_clear"] for row in units)
        form = (all(row["form_clear"] for row in units)
                and len(text.split()) <= cap and len(full.split()) <= 175)
        output[ids] = {"record_points": 28 + optional, "guard_clear": guard,
                       "form_clear": form, "releasable": guard and form,
                       "input_tokens": sum(row["input_tokens"] for row in units),
                       "output_tokens": sum(row["output_tokens"] for row in units), "record": full,
                       "joined_ids": [row["opaque_id"] for row in units]}
    return output


def columns(study_run, modular):
    results = {}
    for method, params in study_run["routes"].items():
        totals = {"record_points": 0., "release_points": 0., "release_probability": 0.,
                  "input_tokens": 0., "output_tokens": 0., "writer_calls": 0.}
        for row in params["cases"]:
            for packet, probability in row["record_distribution"].items():
                block = modular[frozenset(packet.split(","))]
                weight = probability / len(params["cases"])
                totals["record_points"] += weight * block["record_points"]
                totals["release_points"] += weight * block["record_points"] * block["releasable"]
                totals["release_probability"] += weight * block["releasable"]
                totals["input_tokens"] += weight * block["input_tokens"]
                totals["output_tokens"] += weight * block["output_tokens"]
                totals["writer_calls"] += weight * len(block["joined_ids"])
        results[method] = totals
    return results


def outcome_tuned(archival_ids, actual, reference):
    def best(bank):
        rows = []
        for fixed in (True, False):
            candidates = []
            for names in permutations(archival_ids):
                runs = []
                for target, anchor in relay.SCENARIOS:
                    distribution = study.planned_dist(target, anchor, names, bank, not fixed)
                    scores, _ = study.metrics(target, anchor, names, distribution, actual, reference)
                    received = sum(mass * bank[frozenset(names[i] for i in target if i not in pending)]["record_points"]
                                   for pending, (mass, _, _) in distribution.items())
                    runs.append({**scores, "optimized_net": received - scores["communication_cost"]})
                mean = {metric: sum(score[metric] for score in runs) / len(runs) for metric in runs[0]}
                candidates.append({"aliases": names, **mean})
            rows.append((fixed, max(candidates, key=lambda x: x["optimized_net"])))
        return {"fixed_canonical" if fixed else "adaptive_canonical": row for fixed, row in rows}

    return {"raw": best(actual), "release": best({key: {**row, "record_points": row["record_points"] * row["releasable"]}
                                                 for key, row in actual.items()})}


def run():
    review = study.HERE / "receipt-annotations.json"
    ids, records, archived = study.bank(study.EVIDENCE, review)
    primary = transfer.read(study.EVIDENCE / "results.json")
    modular = compose(records)
    return {"scope": "Same model generations. Singleton composition has up to three calls and a larger total cap. "
                     "The posthoc planners see the generated score bank before selecting a route and are diagnostic ceilings "
                     "within their canonical-responder restriction. Neither alters the main comparison.",
            "modular_records": {",".join(sorted(k)): row for k, row in modular.items()},
            "modular_routes": columns(primary, modular),
            "posthoc_planners": outcome_tuned(ids, records, archived)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
