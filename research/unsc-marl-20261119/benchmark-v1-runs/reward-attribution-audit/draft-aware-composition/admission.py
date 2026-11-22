"""Replay held-docket and held-writer admission using matched scored drafts."""

import argparse
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent.parent
REFORM = "reform-2553-transfer/learned-send-writer"
AFG = "afghanistan-2721-source-contrast"
TOLERANCE = "tolerance-2686-transfer/scoped-writer"
DISABILITY = "disability-2475-transfer/scope-bridge"
WRITERS = {"original": "", "authority": "/authority-clarification", "split": "/public-record-anchor"}
FILES = [
    *(f"{REFORM}{suffix}/{file}.json" for suffix in WRITERS.values() for file in ("scores", "verified")),
    f"{AFG}/case.json", f"{AFG}/native-comparison/scores.json",
    *(f"{path}/{file}.json" for path in (TOLERANCE, DISABILITY) for file in ("scores", "verified")),
]
RIDGE = 0.1
MARGIN = 0.5


@dataclass(frozen=True)
class Draft:
    docket: str
    writer: str
    context: str
    fallback: str
    native: str
    baseline: int
    score: int

    @property
    def delta(self):
        return self.score - self.baseline


def load(path):
    return json.loads(path.read_text())


def read(path):
    return load(RUNS / path)


def plan():
    paths = [Path(__file__), HERE / "protocol.md", *(RUNS / file for file in FILES)]
    return {
        "ridge": RIDGE,
        "margin": MARGIN,
        "sha256": {str(path.relative_to(RUNS)): sha256(path.read_bytes()).hexdigest() for path in paths},
    }


def reform_rows():
    split = read(f"{REFORM}/public-record-anchor/scores.json")
    split_packets = read(f"{REFORM}/public-record-anchor/verified.json")["packets"]
    baselines = {}
    for branch in split["branches"]:
        for context, score in zip(branch["pair"], branch["verbatim_scores"], strict=True):
            assert context not in baselines or baselines[context] == score
            baselines[context] = score
    for writer, suffix in WRITERS.items():
        archive = read(f"{REFORM}{suffix}/scores.json")
        records = read(f"{REFORM}{suffix}/verified.json")["packets"]
        assert set(archive["grades"]) == set(records) == set(baselines) == set(split["verbatim_records"])
        for context, grade in archive["grades"].items():
            assert records[context]["visible_sources"] == split_packets[context]["visible_sources"]
            yield Draft("2553", writer, context, split["verbatim_records"][context],
                        records[context]["reply"]["text"], baselines[context], grade["released_70"])


def afghanistan_rows():
    case = read(f"{AFG}/case.json")
    grades = read(f"{AFG}/native-comparison/scores.json")["grades"]
    for context, grade in grades["verbatim_plus_native"].items():
        parts = list(case["public"])
        for index, key in zip(context.split("/"), ("early_statements", "late_clauses"), strict=True):
            if index != "None":
                parts.append(case[key][int(index)])
        fallback = "\n\n".join(part["text"] for part in parts)
        baseline = grades["verbatim"][context]["released"]
        assert baseline == sum(part["weight"] for part in parts)
        assert grade["text"] == fallback or grade["text"].startswith(fallback + "\n\n")
        yield Draft("2721", "append", context, fallback, grade["text"], baseline, grade["released"])


def mask_rows(docket, path, fallback, writers):
    grades = read(f"{path}/scores.json")["scores"]
    records = read(f"{path}/verified.json")["records"]
    for writer, prefix in writers.items():
        for mask in range(8):
            context = f"mask-{mask}"
            native_key = f"{prefix}/{context}"
            fallback_key = f"{fallback}/{context}"
            yield Draft(docket, writer, context, records[fallback_key]["text"],
                        records[native_key]["text"],
                        grades[fallback_key]["score"]["released_70"],
                        grades[native_key]["score"]["released_70"])


def features(row, draft_aware):
    base = Counter(re.findall(r"\w+", row.fallback.lower()))
    if not draft_aware:
        return [base.total()]
    native = Counter(re.findall(r"\w+", row.native.lower()))
    base_nums = set(re.findall(r"\d+", row.fallback))
    native_nums = set(re.findall(r"\d+", row.native))
    return [base.total(), native.total(), native.total() - base.total(),
            (base & native).total() / base.total(),
            (native - base).total() / max(native.total(), 1),
            len(native_nums - base_nums), len(base_nums - native_nums),
            row.native.startswith(row.fallback)]


def weights(rows):
    counts = Counter((row.docket, row.writer) for row in rows)
    writers = Counter(docket for docket, _ in counts)
    result = np.array([1 / (writers[row.docket] * counts[row.docket, row.writer]) for row in rows])
    return result / result.sum()


def predict(train, held, draft_aware):
    x = np.array([features(row, draft_aware) for row in train])
    y = np.array([row.delta for row in train])
    mass = weights(train)
    mean = mass @ x
    variation = np.sqrt(mass @ (x - mean) ** 2)
    active = variation > 1e-9
    z = (x[:, active] - mean[active]) / variation[active]
    centered = y - mass @ y
    coeff = np.linalg.solve(z.T @ (mass[:, None] * z) + RIDGE * np.eye(z.shape[1]), z.T @ (mass * centered))
    held_x = np.array([features(row, draft_aware) for row in held])
    held_z = (held_x[:, active] - mean[active]) / variation[active]
    return mass @ y + held_z @ coeff


def evaluate(train, held):
    baseline = np.array([row.baseline for row in held])
    delta = np.array([row.delta for row in held])
    predictions = {name: predict(train, held, aware)
                   for name, aware in (("fallback_length", False), ("draft_aware", True))}
    decisions = {name: predicted > MARGIN for name, predicted in predictions.items()}
    decisions.update(fallback=np.zeros_like(delta, dtype=bool),
                     native=np.ones_like(delta, dtype=bool), oracle=delta > MARGIN)
    mass = weights(held)
    return {
        "training": {"drafts": len(train), "improved": sum(row.delta > 0 for row in train)},
        "held": {"drafts": len(held), "improved": int(sum(delta > 0)), "harmful": int(sum(delta < 0))},
        "policies": {
            name: {"release": round(float(mass @ (baseline + choice * delta)), 8),
                   "admitted": int(sum(choice)), "improvements_kept": int(sum(choice & (delta > 0))),
                   "harmful_admissions": int(sum(choice & (delta < 0)))}
            for name, choice in decisions.items()
        },
        "rows": [
            {"writer": row.writer, "context": row.context, "fallback": row.baseline, "native": row.score,
             "predicted_delta": {name: round(float(values[i]), 8) for name, values in predictions.items()}}
            for i, row in enumerate(held)
        ],
    }


def run():
    assert plan() == load(HERE / "plan.json")
    groups = {
        "2553": list(reform_rows()),
        "2721": list(afghanistan_rows()),
        "2686": list(mask_rows("2686", TOLERANCE, "verbatim", {"scoped": "scoped"})),
        "2475": list(mask_rows("2475", DISABILITY, "authored/none", {
            "plain": "authored/plain", "scope": "authored/scope",
        })),
    }
    rows = [row for group in groups.values() for row in group]
    assert len(rows) == 69 and len({(r.docket, r.writer, r.context) for r in rows}) == len(rows)
    assert all(r.fallback and 0 <= r.baseline <= 70 and 0 <= r.score <= 70 for r in rows)
    return {
        "held_docket": {docket: evaluate([r for r in rows if r.docket != docket], held)
                        for docket, held in groups.items()},
        "held_2553_writer": {
            writer: evaluate([r for r in rows if r.docket != "2553" or r.writer != writer],
                             [r for r in groups["2553"] if r.writer == writer])
            for writer in WRITERS
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
