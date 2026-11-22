"""Replay a matched request intervention on a frozen climate routing policy."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import routing_climate_language_channel as channel
import routing_climate_transfer as transfer

read, digest, runner = transfer.read, transfer.digest, transfer.runner
ARMS = ("received", "erased")
NOTE_LIMIT, QUESTION_LIMIT = 55, 25


def plan():
    frozen = read(channel.PLAN)
    assert frozen == transfer.per_case_plans()
    (ask, send, reply), swapped, weight = max(frozen["plans"]["learned"], key=lambda row: row[2])
    requester, responder = 1, 3
    target, outgoing = ask[requester], send[requester]
    assert (outgoing, target, reply[responder][0], reply[responder][target]) == (1, 2, 1, 2)
    return {"component_weight": weight, "swapped": swapped, "requester_inventory": requester,
            "responder_inventory": responder, "question_target": target, "requester_sends": outgoing,
            "typed_replies": {"received": target, "erased": reply[responder][0]},
            "world_selection": "Highest-mass component. Smallest requester and responder masks with a duplicated "
                               "Russian default, a request for India, and both sources reachable when received."}


def sources(mask):
    return [source for index, source in enumerate(transfer.task()["optional_sources"]) if mask & (1 << index)]


def request(name, cap, system, payload, evidence_ids):
    return {"id": name, "cap": cap, "evidence_ids": evidence_ids, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]}


def opening():
    p = plan()
    source, = sources(p["requester_inventory"])
    target, = sources(1 << (p["question_target"] - 1))
    note = next(row for row in channel.note_requests() if row["evidence_ids"] == [source["id"]])
    question = request("question", 48,
                       "Write one question to another records desk asking for the named delegation's explanation "
                       "of its vote. Ask for its institutional concerns and preferred scope. Do not supply an answer "
                       "or speculate about the position. Use no more than 25 words. Output only the question.",
                       {"delegation_to_ask_about": target["role"]}, [])
    return note, question


def admit_question(row):
    value = row["output"]
    if row["ended"] and len(value.split()) <= QUESTION_LIMIT and value.count("?") == 1 and value.endswith("?"):
        return value
    return ""


def replies(question):
    inventory = sources(plan()["responder_inventory"])
    guide = (
        "You are a records desk. Send a note based on one annex in your inventory. "
        "If the incoming question asks about a delegation whose annex you hold, use that delegation's annex. "
        "Otherwise use the first annex. Copy the chosen annex ID on its own first line. Then give the named "
        "delegation's explanation in complete sentences, using at most 55 words and only the chosen annex. "
        "Preserve the institutional rationale and the geographic and policy scope."
    )
    return [request(f"reply-{arm}", 96, guide,
                    {"incoming_question": admit_question(question) if arm == "received" else "",
                     "local_inventory": [{key: source[key] for key in ("id", "role", "text")} for source in inventory]},
                    [source["id"] for source in inventory]) for arm in ARMS]


def admit_note(row, attribution=None):
    if attribution is None:
        attribution, _, content = row["output"].partition("\n")
        if attribution.strip() not in row["evidence_ids"]:
            return None
        attribution = attribution.strip()
    else:
        content = row["output"]
    if not row["ended"]:
        return None
    text = content.strip()
    retained = []
    for part in re.split(r"(?<=[.!?])\s+", text):
        if not part.endswith((".", "!", "?")) or len(" ".join([*retained, part]).split()) > NOTE_LIMIT:
            break
        retained.append(part)
    if not retained:
        return None
    prefix = " ".join(retained)
    assert text.startswith(prefix)
    return attribution, prefix


def receipt(outgoing, reply):
    notes = {}
    for entry in (admit_note(outgoing, outgoing["evidence_ids"][0]), admit_note(reply)):
        if entry is not None:
            key, body = entry
            notes.setdefault(key, []).append(body)
    return {source["id"]: "\n".join(notes[source["id"]]) for source in transfer.task()["optional_sources"]
            if source["id"] in notes}


def chairs(outgoing, responses):
    candidates = {tuple(row["evidence_ids"]): row for row in transfer.requests() if row["id"].startswith("visible-")}
    rows = []
    for arm in ARMS:
        delivered = receipt(outgoing, responses[f"reply-{arm}"])
        if not delivered:
            continue
        template = candidates[tuple(delivered)]
        payload = json.loads(template["messages"][1]["content"])
        payload["annexes_delivered"] = delivered
        rows.append(request(f"chair-{arm}", template["cap"], template["messages"][0]["content"],
                            payload, list(delivered)))
    return rows


def episode(generate):
    outgoing, query = opening()
    first = generate([outgoing])
    question = generate([query])
    answers = generate(replies(question[query["id"]]))
    final_requests = chairs(first[outgoing["id"]], answers)
    records = generate(final_requests) if final_requests else {}
    return [{"family": transfer.task()["id"], "final": {**first, **question, **answers, **records}}]


def locks():
    return {**channel.locks(), "live_exchange": digest(Path(__file__))}


def run(directory):
    assert plan()
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(channel.BASE / "launch.json")["model"]), directory)


def verify(directory):
    from transformers import AutoTokenizer

    launch = read(directory / "launch.json")
    trace = directory / "transcript.jsonl"
    done = read(directory / "complete.json")
    finals = directory / "final-records.json"
    assert launch["sha256"] == locks()
    assert done["transcript_sha256"] == digest(trace) and done["final_records_sha256"] == digest(finals)
    observed = iter(map(json.loads, trace.read_text().splitlines()))
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")

    def replay(batch):
        results = {}
        for expected in batch:
            row = next(observed)
            assert all(row[key] == value for key, value in expected.items())
            assert row["input_ids"] == runner.encode(tokenizer, expected)
            ids = row["output_ids"]
            assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1]
            assert row["ended"] == (ids[-1] == eos)
            assert row["output"] == tokenizer.decode(ids, skip_special_tokens=True).strip()
            results[row["id"]] = row
        return results

    result, = episode(replay)
    rows = result["final"]
    assert next(observed, None) is None and len(rows) == done["records"]
    assert read(finals) == {result["family"]: {key: row["output"] for key, row in rows.items()}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "run", "verify"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        result = plan() if args.mode == "plan" else {
            key: {**{field: row[field] for field in ("ended", "evidence_ids", "output")},
                  "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
            for key, row in verify(args.directory).items()}
        print(json.dumps(result, ensure_ascii=False, indent=2))
