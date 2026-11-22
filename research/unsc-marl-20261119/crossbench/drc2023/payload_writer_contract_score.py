"""Compare source-clause drafting, the original writer and exact rendering."""
import json
from pathlib import Path
from unittest.mock import patch

import payload_policy_evaluate as evaluator
import payload_writer_contract as contract

HERE = contract.HERE
protocol = evaluator.protocol
REVIEW = HERE / "payload-writer-contract-review.json"


def exact_records(rows, tokenizer):
    result = {}
    canonical = dict(zip(contract.previous.SOURCE_IDS, contract.previous.passages(), strict=True))
    for row in rows.values():
        available = row["seen"]
        text = "\n\n".join(canonical[key] for key in available) or "No additional source detail was delivered."
        given = json.loads(row["messages"][1]["content"])["working_notes"]
        assert given == [canonical[key] for key in available]
        held = frozenset(contract.previous.SOURCE_IDS.index(key) for key in available)
        facts = sorted(fact for fact, key in evaluator.FACT_SOURCE.items() if key in available)
        words = len(text.split())
        output_tokens = len(contract.previous.channel.payload_tokens(tokenizer, text))
        assert words <= 73 and output_tokens <= row["cap"]
        result[held] = {"licensed": len(facts), "facts": facts, "unlicensed": [], "exact_fields": list(available),
                        "conflicts": [], "safe_complete": True, "words": words, "output_tokens": 0,
                        "rendered_text_tokens": output_tokens, "ended": True, "text": text}
    return result


def variants(learned, focus, prior):
    _, exact = protocol.best_script(focus, prior, protocol.PEER)
    _, independent = protocol.best_script(focus, prior, 0)
    return {
        "learned": (learned, protocol.PEER),
        "learned_no_peer": (learned, 0.),
        "greedy": (protocol.greedy(focus), protocol.PEER),
        "best_independent": (independent, 0.),
        "optimized_interactive": (exact, protocol.PEER),
    }


def summarize(learned, writer_tables, baseline):
    output = {}
    for name in ("training", "overlap", "split"):
        prior = protocol.roster(name)
        rows = {variant: [] for variant in writer_tables}
        for focus in protocol.PAIRS:
            options = variants(learned, focus, prior)
            for variant, table in writer_tables.items():
                rows[variant].append({option: evaluator.generated(weights, focus, prior, peer, table)
                                      for option, (weights, peer) in options.items()})
        replay = {variant: {
            option: {key: sum(row[option][key] for row in measurements) / len(measurements)
                     for key in values} for option, values in measurements[0].items()
        } for variant, measurements in rows.items()}
        # Exact extraction should preserve the complete policy objective.
        prefix = baseline["inventories"][name]["mean"]
        for model_policy, recorded in (("learned", "learned"), ("greedy", "greedy"),
                                       ("optimized_interactive", "best_interactive")):
            old_delivery = prefix[recorded]["net"]
            assert abs(replay["exact_renderer"][model_policy]["preserved_field_net"] - old_delivery) < 1e-9
        output[name] = replay
    return output


def run():
    raw, tokenizer = contract.replay(contract.ROOT)
    annotations = contract.previous.interface.parent.read(REVIEW)
    with patch.object(evaluator, "REVIEW", REVIEW), patch.object(evaluator.writer, "EVIDENCE", contract.ROOT):
        learned_writer = evaluator.terminal(raw)
    renderer = exact_records(raw, tokenizer)
    fit = json.loads(evaluator.POLICY.read_text())

    def freeze(value):
        return tuple(map(freeze, value)) if isinstance(value, list) else value
    learned = {freeze(row["state"]): row["probabilities"] for row in fit["policy"]}
    original = contract.previous.interface.parent.read(
        contract.previous.EVIDENCE / "results.json")
    tables = {"separate_clause_writer": learned_writer, "exact_renderer": renderer}
    measured = summarize(learned, tables, fit)
    for prior, result in measured.items():
        result["original_writer"] = original["inventories"][prior]["mean"]
    terminal = {}
    for held in renderer:
        label = ",".join(contract.previous.SOURCE_IDS[i] for i in sorted(held)) or "public"
        terminal[label] = {variant: table[held] for variant, table in tables.items()}
        terminal[label]["original_writer"] = original["terminal_sets"][label]
    return {"scope": "Frozen routing policies and identical documentary cards. The Qwen prompt changes to retain "
                     "source-specific legal force and keep notes separate. The deterministic comparator copies "
                     "all admitted notes and emits no extra legal claims. Same-assistant reviewed synthesis.",
            "terminal_records": terminal, "inventories": measured, "annotations": annotations}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
