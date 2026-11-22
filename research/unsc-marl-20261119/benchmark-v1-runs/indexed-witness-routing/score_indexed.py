"""Compare resolved source evidence, scope verification and terminal scores."""
import json

from indexed_study import HERE, PRIOR, locked, old, read


def mean_margin(verification, labels):
    margins = []
    for suffix, meaning in labels.items():
        logits = verification[suffix]["logits"]
        yes = next(k for k in meaning if meaning[k] == "supported")
        no = next(k for k in meaning if meaning[k] == "unsupported")
        margins.append(logits[yes] - logits[no])
    return sum(margins) / len(margins)


def outcome_table():
    reform = read(old.REFORM / "results.json")["cases"]
    afghanistan = read(old.AFGHAN / "results.json")["cases"]
    outcomes = {"reform/" + k: [v["records"][arm]["released_70"] for arm in ("fund", "process")]
                for k, v in reform.items()}
    outcomes.update({"afghanistan/" + k: [v["records"][arm]["grade"]["released_70"] for arm in ("fund", "process")]
                     for k, v in afghanistan.items()})
    return outcomes | {"afghanistan/russia-agreement-deletion": [40, 40]}


def run():
    spec = locked()
    archive = read(HERE / "verified.json")
    marks = read(HERE / "marks.json")
    previous = read(PRIOR / "results.json")["cases"]
    outcomes = outcome_table()
    assert archive["cases"].keys() == marks.keys() == previous.keys() == outcomes.keys()
    results = {}
    for key, row in archive["cases"].items():
        source = spec["views"][key]["text"]
        span = row["span"]
        verification = row["verification"]
        if span:
            assert source[span["start"]:span["stop"]] == span["text"]
            assert mark_is_allowed(marks[key], span)
            assert verification.keys() == {"prior", "necessary"}
        else:
            assert not marks[key]["sufficient"] and not verification
        margins = {arm: mean_margin(replies, spec["labels"]) for arm, replies in verification.items()}
        decisions = previous[key]["decisions"] | {
            "indexed_range": bool(span),
            "indexed_and_prior_verifier": bool(span and margins["prior"] > 0),
            "indexed_and_necessary_verifier": bool(span and margins["necessary"] > 0),
            "indexed_and_assistant": marks[key]["sufficient"],
        }
        results[key] = {
            "target": previous[key]["target"], "span": span, "id_reply": row["id_reply"]["text"],
            "margins": margins, "review": marks[key], "choices": decisions,
            "release": {arm: outcomes[key][int(answer)] if answer is not None else None
                        for arm, answer in decisions.items()},
        }
    totals = {}
    for name in ("all_original", "reform", "afghanistan", "all_with_deletion"):
        rows = [v for key, v in results.items() if name == "all_with_deletion"
                or (not key.endswith("deletion") and (name == "all_original" or key.startswith(name + "/")))]
        totals[name] = {}
        for arm in rows[0]["choices"]:
            observed = [r for r in rows if r["choices"][arm] is not None]
            totals[name][arm] = {
                "correct": sum(r["choices"][arm] == r["target"] for r in observed),
                "n": len(observed), "false_support": sum(r["choices"][arm] and not r["target"] for r in observed),
                "missed_support": sum(not r["choices"][arm] and r["target"] for r in observed),
                "mean_release": round(sum(r["release"][arm] for r in observed) / len(observed), 8),
            }
    return {"calls": archive["calls"], "cases": results, "summary": totals}


def mark_is_allowed(mark, span):
    return not mark["sufficient"] or bool(mark["witness"] and mark["witness"] in span["text"])


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
