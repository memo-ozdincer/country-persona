"""Measure whether terminal documentary rewards identify the direction of a message effect."""
import argparse
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
REFORM = RUNS / "reform-2553-transfer/learned-send-writer"
FILES = {
    "reform_original": REFORM / "scores.json",
    "reform_clarified": REFORM / "authority-clarification/scores.json",
    "reform_split": REFORM / "public-record-anchor/scores.json",
    "reform_plan": REFORM / "plan.json",
    "disability": RUNS / "disability-2475-transfer/scope-bridge/scores.json",
    "tolerance_original": RUNS / "tolerance-2686-transfer/scores.json",
    "tolerance_revised": RUNS / "tolerance-2686-transfer/writer-revision/scores.json",
    "tolerance_scoped": RUNS / "tolerance-2686-transfer/scoped-writer/scores.json",
}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    paths = [Path(__file__), HERE / "protocol.md", *FILES.values()]
    return {"sha256": {str(p.relative_to(RUNS)): sha(p) for p in paths}}


@dataclass(frozen=True)
class Score:
    nominal: float
    lower: float
    upper: float
    uncertain_guard: bool

    @classmethod
    def archive(cls, row):
        raw_low, raw_high = row["raw_70"]
        blocked = row["release_blockers"]
        if row["release"]:
            assert not blocked and row["released_70"] == raw_low
            return cls(raw_low, raw_low, raw_high, False)
        assert blocked and row["released_70"] == 0
        uncertain = blocked == ["guard_uncertain"]
        return cls(0, 0, raw_high if uncertain else 0, uncertain)


def contrast(coefficients, values):
    # A repeated prompt has one output and one grade. Combine its signed masses first.
    nominal, lower, upper = 0., 0., 0.
    for key, weight in coefficients.items():
        entry = values[key]
        nominal += weight * entry.nominal
        lower += weight * (entry.lower if weight >= 0 else entry.upper)
        upper += weight * (entry.upper if weight >= 0 else entry.lower)
    assert lower <= nominal <= upper
    return {"nominal": nominal, "band": [lower, upper]}


def across(writers):
    lo = min(row["band"][0] for row in writers.values())
    hi = max(row["band"][1] for row in writers.values())
    if lo > 0:
        direction = "prefer_add_or_replace"
    elif hi < 0:
        direction = "prefer_original"
    elif lo == hi == 0:
        direction = "tie"
    else:
        direction = "abstain"
    return {"band": [lo, hi], "direction": direction}


def reform():
    base = read(FILES["reform_plan"])
    coefficients = {}
    for row in base["branches"]:
        if not row["pair"]:
            continue
        for sign, key in zip((-1, 1), row["pair"], strict=True):
            coefficients[key] = coefficients.get(key, 0.) + sign * row["probability"]

    assert sum(coefficients.values()) == 0.
    output = {}
    for name in ("original", "clarified", "split"):
        archive = read(FILES[f"reform_{name}"])
        assert set(coefficients) == set(archive["grades"])
        weights = {key: Score.archive(row) for key, row in archive["grades"].items()}
        audited = contrast(coefficients, weights)
        assert audited["nominal"] == archive["expected_differences"]["writer_released"]
        uncertain = [key for key, row in weights.items() if row.uncertain_guard]
        sensitivity = []
        for choices in product((False, True), repeat=len(uncertain)):
            cleared = [key for key, decision in zip(uncertain, choices, strict=True) if decision]
            valid = dict(weights)
            for key in uncertain:
                if key in cleared:
                    lo, hi = archive["grades"][key]["raw_70"]
                    valid[key] = Score(lo, lo, hi, False)
                else:
                    valid[key] = Score(0, 0, 0, False)
            sensitivity.append((cleared, contrast(coefficients, valid)["band"]))
        archived = {frozenset(row["cleared"]): row["release_delta_bounds"]
                    for row in archive["guard_sensitivity"]}
        assert {frozenset(cleared): band for cleared, band in sensitivity} == archived
        flips = [{"cleared": cleared, "band": band} for cleared, band in sensitivity if band[1] < 0]
        minimal = min((len(row["cleared"]) for row in flips), default=None)
        output[name] = audited | {
            "smallest_strict_reversals": [row for row in flips if len(row["cleared"]) == minimal],
            "largest_branch_packet_mass": max(abs(c) for c in coefficients.values()),
        }
    comparator = read(FILES["reform_split"])["expected"]
    references = {key: comparator[key]["unconditional_paired_delta"]
                  for key in ("verbatim_delegation_notes", "authored_comparisons")}
    return {"native": output, "cross_writer": across(output), "references": references}


def load_bank(archive, vector, prefix=""):
    results = {}
    for mask in range(8):
        entry = archive["scores"][f"{prefix}mask-{mask}"]
        results[mask] = Score.archive(entry["score"])
        assert results[mask].nominal == vector[mask]
    return results


def edges(banks, reference):
    results = []
    for mask, bit in product(range(8), range(3)):
        if mask & (1 << bit):
            continue
        next_mask = mask | (1 << bit)
        outcomes = {name: contrast({mask: -1, next_mask: 1}, values) for name, values in banks.items()}
        results.append({"before": mask, "after": next_mask, "added_note": bit,
                        "reference_nominal": outcomes[reference]["nominal"],
                        "writers": outcomes, "cross_writer": across(outcomes)})
    assert len(results) == 12
    directions = ("prefer_add_or_replace", "prefer_original", "tie", "abstain")
    return {
        "rows": results,
        "counts": {direction: sum(row["cross_writer"]["direction"] == direction for row in results)
                   for direction in directions},
        "positive_reference": sum(row["reference_nominal"] > 0 for row in results),
        "positive_reference_with_possible_reversal": sum(
            row["reference_nominal"] > 0 and row["cross_writer"]["band"][0] < 0 for row in results),
        "opposite_nominal_signs_across_writers": sum(
            min(x["nominal"] for x in row["writers"].values()) < 0 <
            max(x["nominal"] for x in row["writers"].values()) for row in results),
    }


def disability():
    archive = read(FILES["disability"])
    banks = {name: load_bank(archive, archive["banks"][f"authored/{name}"], f"authored/{name}/")
             for name in ("none", "plain", "scope")}
    return edges(banks, "none")


def tolerance():
    banks = {}
    for name in ("original", "revised"):
        archive = read(FILES[f"tolerance_{name}"])
        banks[name] = load_bank(archive, archive["score_bank"])
    archive = read(FILES["tolerance_scoped"])
    banks.update({name: load_bank(archive, archive["banks"][name], f"{name}/")
                  for name in ("scoped", "verbatim")})
    return {"all_writers": edges(banks, "original"),
            "free_form": edges({k: banks[k] for k in ("original", "revised")}, "original"),
            "source_scoped": edges({k: banks[k] for k in ("scoped", "verbatim")}, "verbatim")}


def run():
    lock = HERE / "plan.json"
    assert read(lock) == plan()
    return {"plan_sha256": sha(lock), "2553_replacement": reform(),
            "2475_marginal_delivery": disability(), "2686_marginal_delivery": tolerance()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
