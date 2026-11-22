"""Score decisions, visible evidence, and protected terminal records independently."""
import json

from collect_witnesses import AFGHAN, HERE, REFORM, locked, read


def verify_span(verdicts, mappings):
    if not verdicts:
        return None
    assert verdicts.keys() == mappings.keys()
    margins = []
    for order, labels in mappings.items():
        scores = verdicts[order]["logits"]
        support = next(letter for letter, role in labels.items() if role == "supported")
        reject = next(letter for letter, role in labels.items() if role == "unsupported")
        margins.append(scores[support] - scores[reject])
    return sum(margins) / len(margins)


def run():
    extract = read(HERE / "verified.json")
    marks = read(HERE / "marks.json")
    spec = locked()
    assert extract["cases"].keys() == marks.keys() == spec["views"].keys()
    archive = {
        "reform": read(REFORM / "results.json")["cases"],
        "afghanistan": read(AFGHAN / "results.json")["cases"],
    }
    rows = {}
    for key, result in extract["cases"].items():
        family, view = key.split("/")
        mark = marks[key]
        native = result["extraction"]["text"]
        witness = result["exact_span"]
        verdict = verify_span(result["verification"], spec["labels"])
        assert (verdict is None) == (not witness)
        assert not mark["sufficient"] or witness
        assert not witness or witness in spec["views"][key]["text"]
        prior = archive[family].get(view)
        if family == "reform":
            target = "gb-process" in prior["grounded_card_ids"]
            outcomes = [prior["records"][role]["released_70"] for role in ("fund", "process")]
            old = prior["choices"]["claim_mean"]["action"] == "process"
        elif prior:
            target = prior["condition_supported"]
            outcomes = [prior["records"][role]["grade"]["released_70"] for role in ("fund", "process")]
            old = prior["choices"]["claim_at_zero"]["classified_support"]
        else:
            assert view == "russia-agreement-deletion"
            target, outcomes, old = False, [40, 40], None
        decisions = {
            "old_full_message_claim": old,
            "extractor_non_none": bool(native.strip() and native != "NONE"),
            "exact_span": bool(witness),
            "exact_span_and_verifier": bool(witness and verdict > 0),
            "exact_span_and_assistant": mark["sufficient"],
        }
        rows[key] = {
            "target": target, "reply_text": native, "witness": witness,
            "mean_support": verdict, "assistant_mark": mark,
            "decisions": decisions, "release": {policy: outcomes[int(answer)] if answer is not None else None
                                                for policy, answer in decisions.items()},
        }
    totals = {}
    for group in ("all_original", "reform", "afghanistan", "all_with_deletion"):
        cases = [row for name, row in rows.items()
                 if (group == "all_original" and not name.endswith("deletion"))
                 or (group == "all_with_deletion")
                 or (name.startswith(group + "/") and not name.endswith("deletion"))]
        totals[group] = {}
        for policy in cases[0]["decisions"]:
            seen = [row for row in cases if row["decisions"][policy] is not None]
            totals[group][policy] = {
                "correct": sum(row["decisions"][policy] == row["target"] for row in seen),
                "n": len(seen),
                "false_support": sum(row["decisions"][policy] and not row["target"] for row in seen),
                "missed_support": sum(not row["decisions"][policy] and row["target"] for row in seen),
                "mean_release": round(sum(row["release"][policy] for row in seen) / len(seen), 8),
            }
    return {"calls": extract["calls"], "cases": rows, "summary": totals}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
