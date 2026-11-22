"""Replay language-conditioned coordination through reviewed DRC terminal records."""
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import receipt_ack_binding as decoder
import payload_writer_contract_score as writer

HERE = decoder.HERE
game = decoder.previous.experiment
base = game.base
BANK = HERE / "payload-writer-contract-evidence/results.json"
RECEIPTS = HERE / "receipt-ack-binding-evidence/results.json"
# Match decoded fields to the verified writer's cards, not to its option order.
CARDS = ("reports", "updates", "mandate", "review")
PAIR_NAMES = {names: "+".join(CARDS[i] for i in names) for names in base.PAIRS}


def load(path):
    return json.loads(path.read_text())


def terminal_banks():
    data = load(BANK)["terminal_records"]
    frozen = load(writer.contract.ROOT / "final-records.json")["drc-legal-force-contract"]
    original = load(writer.contract.previous.EVIDENCE / "final-records.json")["drc-terminal-extract"]
    assert data.keys() == frozen.keys() == original.keys()
    compiled = {}
    for label, writers in data.items():
        stored = [] if label == "public" else label.split(",")
        held = frozenset(CARDS.index(card) for card in stored)
        docs = {variant: row | {
            "text": frozen[label] if variant == "separate_clause_writer" else
                    original[label] if variant == "original_writer" else row["text"]
        } for variant, row in writers.items()}
        assert all(set(row["exact_fields"]) <= set(stored) for row in docs.values())
        for entry in docs.values():
            assert len(entry["text"].split()) == entry["words"]
        compiled[held] = docs
    assert set(compiled) == {frozenset(c) for k in range(3) for c in combinations(range(4), k)}
    return compiled


def distribution(policy, focus, prior, mode, mapping, link):
    delivered_worlds = defaultdict(float)
    for (left, right), prior_p in prior.items():
        for first, a in base.choose_probability(policy, "sender", focus, left):
            if not a:
                continue
            for first_ok, seen, chance in game.events(first, mode, link):
                if not chance:
                    continue
                for second, b in base.choose_probability(policy, "recipient", focus, right, mapping[seen]):
                    if not b:
                        continue
                    for second_ok, reply_p in ((True, link), (False, 1 - link)):
                        held = frozenset(slot for slot, arrived in ((first, first_ok), (second, second_ok)) if arrived)
                        delivered_worlds[held] += prior_p * a * chance * b * reply_p
    assert abs(sum(delivered_worlds.values()) - 1) < 1e-9
    return delivered_worlds


def score(receipts, focus, compiled):
    target = {CARDS[i] for i in focus}
    strict_delivery = sum(p for held, p in receipts.items() if frozenset(focus) <= held)
    writers = {}
    for variant in next(iter(compiled.values())):
        sums = defaultdict(float)
        for held, p in receipts.items():
            terminal = compiled[held][variant]
            present = target & set(terminal["exact_fields"])
            sums["target_clauses_preserved"] += p * len(present)
            sums["supported_facts"] += p * len(terminal["facts"])
            sums["safe_and_complete"] += p * (present == target and terminal["safe_complete"])
            sums["guard_clear"] += p * terminal["safe_complete"]
        writers[variant] = dict(sums)
    assert abs(writers["exact_renderer"]["safe_and_complete"] - strict_delivery) < 1e-9
    return {"both_clauses_delivered": strict_delivery, "writers": writers}


def run():
    compiled = terminal_banks()
    learned = game.stored(decoder.previous.POLICY)
    rows = load(RECEIPTS)["examples"]["drc"]
    mode = {method: {row["field"]: row[method] if row[method] in range(4) else None
                     for row in rows if row["kind"] == "received"} | {None: None}
            for method in ("joint", "separate")}
    correct = {k: k for k in (None, *range(4))}
    erased = dict.fromkeys(correct)
    link = base.CHAIR
    results = {}
    for prior_name in ("overlap", "split"):
        prior = base.roster(prior_name)
        cases = {}
        for focus in base.PAIRS:
            ack_bound, ack = game.exact(focus, prior, "ack", link)
            silent_bound, silent = game.exact(focus, prior, "silent", link)
            variants = {"typed_learned": (learned, "ack", correct),
                        "joint_read": (learned, "ack", mode["joint"]),
                        "separate_read": (learned, "ack", mode["separate"]),
                        "erased_read": (learned, "ack", erased),
                        "exact_ack": (ack, "ack", correct), "exact_silent": (silent, "silent", correct)}
            packet = {name: score(distribution(policy, focus, prior, protocol, decode, link), focus, compiled)
                      for name, (policy, protocol, decode) in variants.items()}
            assert abs(packet["exact_ack"]["both_clauses_delivered"] - ack_bound) < 1e-9
            assert abs(packet["exact_silent"]["both_clauses_delivered"] - silent_bound) < 1e-9
            # With one attempt per desk, receipt of both target clauses fixes the
            # terminal packet. A writer failure on that packet caps all routing.
            focus_record = compiled[frozenset(focus)]
            cases[PAIR_NAMES[focus]] = {"routing": packet, "target_packet_records": focus_record}
        results[prior_name] = cases
    return {
        "scope": "Frozen learned and exact scripted routing under simulated holdings and losses. "
                 "Decoder errors affect the second desk's choice, while authenticated document IDs determine the chair's received cards. "
                 "The terminal banks are existing first-pass DRC writer outputs and same-assistant review. "
                 "A complete target is two requested clauses, separate from full-record release.",
        "inputs": {str(p.relative_to(HERE.parent)): decoder.previous.sha256(p.read_bytes()).hexdigest()
                   for p in (Path(__file__), BANK, RECEIPTS, decoder.previous.POLICY,
                             writer.contract.ROOT / "final-records.json",
                             writer.contract.previous.EVIDENCE / "final-records.json")},
        "receipt_decode": mode, "split_or_overlap": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
