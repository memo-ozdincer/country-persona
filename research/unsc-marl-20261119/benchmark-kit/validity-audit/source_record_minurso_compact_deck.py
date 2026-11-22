"""Make the matched-criterion packets and token ledger for the compact chair outputs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from source_record_minurso_compact import ARCHIVE, replay
from source_record_minurso_review import final_packet, json_digest
from source_record_run import digest


def prepare(directory):
    original, rows = replay(directory)
    seal = digest(directory / "transcript.jsonl")
    base = json.loads((ARCHIVE / "judge-key.json").read_text())
    original_deck = json.loads((ARCHIVE / "judge-packets.json").read_text())
    assert base["transcript_sha256"] == digest(ARCHIVE / "transcript.jsonl")
    assert base["judge_packets_sha256"] == json_digest(original_deck)
    base_use = {arm: base["diagnostics"][id_] for id_, arm in base["key"].items()}
    deck = {"packets": [], "mechanism": original_deck["mechanism"]}
    key, diagnostics = {}, {}
    for row in rows:
        arm = row["id"].split("/")[1]
        opaque = sha256(f"{seal}/{row['id']}".encode()).hexdigest()[:16]
        deck["packets"].append(final_packet(opaque, row["output"]))
        key[opaque] = arm
        before = original["final"][row["id"]]
        diagnostics[opaque] = {**base_use[arm],
                               "input_tokens": base_use[arm]["input_tokens"] +
                               len(row["input_ids"]) - len(before["input_ids"]),
                               "output_tokens": base_use[arm]["output_tokens"] +
                               len(row["output_ids"]) - len(before["output_ids"]),
                               "ended": row["ended"], "words": len(row["output"].split())}
    deck["packets"].sort(key=lambda packet: packet["id"])
    ledger = {"key": key, "diagnostics": diagnostics, "transcript_sha256": seal,
              "judge_packets_sha256": json_digest(deck)}
    return deck, ledger


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    target = cli.parse_args().directory
    packets, judge_key = prepare(target)
    for name, payload in (("judge-packets.json", packets), ("judge-key.json", judge_key)):
        (target / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
