"""Replay the four live choices with authenticated archival passage transport."""
from hashlib import sha256
import json
from pathlib import Path

import live_protocol as live

HERE = live.HERE
read = live.partner.read
CAP = 65
CHAIR_CAP = 85


def hash_text(text):
    return sha256(text.encode("utf-8")).hexdigest()


def packet(source_id, passage):
    return {"source_id": source_id, "text": passage, "sha256": hash_text(passage)}


def admit(reply, focal_id, local_inventory, registry):
    key, text = reply["source_id"], reply["text"]
    if key != focal_id or key not in local_inventory:
        return None
    if not 0 < len(text.split()) <= CAP:
        return None
    if reply["sha256"] != registry[key] or hash_text(text) != registry[key]:
        return None
    return text


def run():
    task = live.partner.load()
    origins = {focus["id"]: focus["backup"] for focus in task["focuses"]}
    registry = {key: hash_text(text) for key, text in origins.items()}
    bank = read(HERE / "live-evidence/scores.json")
    control = read(HERE / "extractive-evidence/scores.json")["compiled"]
    results, foils = {}, {}
    for case, (_, focal, options) in live.CASES.items():
        focus = task["focuses"][focal]
        keys = [task["focuses"][i]["id"] for i in options]
        result = {}
        for arm, observed in bank["pairs"][case].items():
            source = observed["sent"]
            assert source in keys
            reply = packet(source, origins[source])
            supported = admit(reply, focus["id"], keys, registry)
            supplement = " ".join([focus["slip"], supported]) if supported else focus["slip"]
            assert len(supplement.split()) <= CHAIR_CAP
            recorded = 70 if supported else 42
            assert recorded == control[f"{case}/{arm}"]["strict"]
            result[arm] = {"reply": reply, "received": supported is not None,
                           "note_words": len(reply["text"].split()), "supplement_words": len(supplement.split()),
                           "supplement": supplement, "strict": recorded}
        results[case] = result
        genuine = packet(focus["id"], origins[focus["id"]])
        different = next(key for key in keys if key != focus["id"])
        corrupt_text = genuine["text"] + " It became binding."
        assert len(corrupt_text.split()) <= CAP
        probes = {
            "authentic": (genuine, keys),
            "unrelated": (packet(different, origins[different]), keys),
            "unavailable": (genuine, [different]),
            "tampered_bytes": ({**genuine, "text": corrupt_text}, keys),
            "self_rehashed": (packet(focus["id"], corrupt_text), keys),
            "relabelled_archive": (packet(focus["id"], origins[different]), keys),
        }
        truth = {}
        for name, (reply, inventory) in probes.items():
            accepted = admit(reply, focus["id"], inventory, registry) is not None
            assert accepted == (name == "authentic")
            truth[name] = accepted
        foils[case] = truth
    return {"scope": "Use a registry of archival excerpts approved for the benchmark. Same live source choices and "
                     "word caps. This is a deterministic counterfactual control, with no fresh model generations. "
                     "Transcript authenticity uses exact source bytes and local membership. The rubric witness for each "
                     "trusted excerpt is the previously checked extractive control.",
            "code_sha256": live.partner.digest(Path(__file__)),
            "task_sha256": live.partner.digest(HERE / "task.json"), "verified_source_hashes": registry,
            "source_live_score_sha256": live.partner.digest(HERE / "live-evidence/scores.json"),
            "common_public_record": task["public_record"], "results": results, "integrity_cases": foils}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
