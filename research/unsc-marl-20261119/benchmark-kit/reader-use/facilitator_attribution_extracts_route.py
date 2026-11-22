"""Route actual source-local extracts and score each resulting full-record receipt mask."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_attribution_extracts_score as extracted
import facilitator_receipt_ceiling as ceiling
import facilitator_receipt_search as search
import facilitator_transfer_fit as transfer

study = extracted.study
quality = extracted.brief
record = ceiling.prior.record
MODE = transfer.MODE


def receipt_bank(artifact):
    checked = artifact["witnesses"]
    routes, records = [], {}
    for name, scenario in study.first.panels():
        selected = artifact["records"][name]["selected"]
        real = {f"S{i}": checked.get(f"{name}/S{i}", {}).get("accepted") for i in (1, 2)}
        local = tuple(selected[sid] if exact else "unknown" for sid, exact in real.items())
        truth = scenario["expected"]
        for flags in product((False, True), repeat=2):
            seen = frozenset(i for i, yes in enumerate(flags) if yes)
            citations = {sid: exact for i, (sid, exact) in enumerate(real.items()) if i in seen}
            text, council, fields, statuses = extracted.render(scenario, selected, citations)
            marks = {"council": council, "issue": "", "reason": ""}
            for i, target in enumerate(truth, 1):
                sid = f"S{i}"
                judged = checked.get(f"{name}/{sid}", {}).get("review", {}).get("grounded")
                correct = (statuses[i-1] == target and
                           (target == "unknown" or judged == "yes"))
                marks[f"s{i}"] = fields[sid] if correct else ""
            grade = quality.grade({"output": text, "ended": True}, marks, truth)
            if seen == extracted.BOTH:
                saved = artifact["records"][name]
                assert all(grade[key] == saved[key] for key in grade)
            routes.append((name, MODE, seen, local, grade["expected"], grade["disposition"], grade["strict"]))
            records[f"{name}/{2 * flags[0] + flags[1]}"] = grade
    return transfer.augmented(record.collect(routes)), records


def full_record_reward(entry):
    decision, publication = original_rewards(entry)
    return decision, publication + int(entry["strict"] and entry["expected"] == "withhold")


original_rewards = record.rewards


def report(path):
    parsed = json.loads(path.read_text())
    bank, receipts = receipt_bank(parsed)
    frozen, independent = ceiling.stock()
    policies = (("frozen", "learned", frozen), ("trained_independent", "learned_erased", independent), ("greedy", "greedy", {}))
    evaluations = {}
    with patch.object(record, "MODES", (MODE,)):
        for layout in ("split", "overlap"):
            result = record.evaluate(bank, policies, layout)
            comparative = {}
            for name, acknowledgments in (("adaptive", True), ("independent", False)):
                _, _, matrix = ceiling.tensor(bank, layout, acknowledgments)
                comparative[name] = search.maximize(matrix)["exact_net"]
            values = {name: row["summary"][MODE] for name, row in result.items()}
            full_ceiling = {}
            with patch.object(record, "rewards", full_record_reward):
                for name, acknowledgments in (("adaptive", True), ("independent", False)):
                    _, _, matrix = ceiling.tensor(bank, layout, acknowledgments)
                    full_ceiling[name] = search.maximize(matrix)["exact_net"]
            full_net = {name: row["brief_net"] + row["usable_withhold"] for name, row in values.items()}
            assert max(full_net.values()) <= full_ceiling["adaptive"] + 1e-9
            evaluations[layout] = {"systems": values, "exact_ceilings": comparative,
                                   "reward_strict_withholds": {"policy_net": full_net, "exact_ceilings": full_ceiling}}
    return {
        "scope": "Exact simulated receipt replay with actual separately generated source sentences. Full-record scoring "
                 "uses the original complete-evidence key at every mask. S0 stays public. Omitted evidence is expressed "
                 "as an attributed gap. Both slot orders share one policy. The alternate reward credits strict withholds for the same policies. "
                 "Acknowledgment is free. No new routing fit.",
        "panels": len(bank) // 2, "receipts": receipts, "routing": evaluations,
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), path)},
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("extract_scores", type=Path)
    print(json.dumps(report(p.parse_args().extract_scores), indent=2, ensure_ascii=False))
