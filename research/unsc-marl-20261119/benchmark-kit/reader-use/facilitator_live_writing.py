"""Run new natural-language evidence replies and final Council prose."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_live_delivery as previous

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-live-writing-evidence"
FAMILY = "facilitator-live-writing"
RUNNER = previous.RUNNER
ROUTING = previous.EVIDENCE / "results.json"
ROOT = HERE.parents[1]
PACKETS = {"unifil": ROOT / "crossbench/unifil-record.json",
           "myanmar": ROOT / "crossbench/myanmar/historical-task.json"}
IDS = {"unifil": ("brazil", "china", "russia"), "myanmar": ("uk", "india", "chair")}
PUBLIC = {"unifil": ("vote", "operative"), "myanmar": ("vote", "mandate")}
REPLY = (
    "Send a brief documentary reply for a Council record. Use your own words in one or two sentences, "
    "at most 52 words. Preserve the source's speaker and qualifications exactly in meaning. Distinguish "
    "national statements and procedural acts. Answer from the authorized passage only, even when the "
    "question asks about another topic. If authorization is empty, return exactly NONE."
)
FINAL = (
    "Write a retrospective Security Council record in no more than 175 words. Use only the delivered "
    "sources. State the exact adopted act and roll call, the operative scope, and each position or "
    "qualification established by the sources. Distinguish Council authority and national positions. "
    "Where both relevant statements arrive, explain their agreement and difference. Cite source IDs in "
    "square brackets directly after material facts. Give only the final record."
)


def load(path):
    return json.loads(path.read_text())


def dossier(name):
    case = load(PACKETS[name])
    return case, {row["id"]: row["text"] for row in case["evidence"]}


def episodes():
    earlier = load(ROUTING)["episodes"]
    for key, name, info in previous.episodes():
        archived = earlier[key]
        assert info["inventory"] == archived["inventory"] and info["opening_receipts"] == archived["opening_receipts"]
        yield key, name, archived


def tasks():
    for key, name, case in episodes():
        sources = dossier(name)[1]
        grouped = {}
        for arm, result in case["arms"].items():
            card = result["requested_send"]
            if card:
                assert previous.ROUTE.SEND[case["inventory"][1], card]
            source = sources[IDS[name][card - 1]] if card else ""
            identity = (result["question"], source)
            group = grouped.setdefault(identity, {"id": f"{key}/reply/{len(grouped)}", "arms": []})
            group["arms"].append(arm)
        for (question, source), group in grouped.items():
            yield group["id"], name, group["arms"], question, source


def reply_requests():
    for key, _, _, question, source in tasks():
        yield previous.prompt(key, 92, REPLY, {"received_question": question, "authorized_source": source})


def final_views(rows):
    replies = {(key.rsplit("/", 2)[0], arm): key for key, _, arms, *_ in tasks() for arm in arms}
    for key, name, case in episodes():
        task, sources = dossier(name)
        before = case["opening_receipts"]
        stable = {sid: sources[sid] for sid in PUBLIC[name]}
        stable.update({sid: sources[sid] for i, sid in enumerate(IDS[name]) if before & (1 << i)})
        views = {}
        for arm, prior in case["arms"].items():
            reply_id = replies[key, arm]
            source = prior["requested_send"]
            raw = rows[reply_id]
            for mode in ("live", "direct"):
                shown = stable.copy()
                # Preserve both copies if the final send repeats an opening
                # source. Its already delivered content stays available.
                if source:
                    sid = IDS[name][source - 1]
                    if mode == "direct":
                        shown[sid] = sources[sid]
                    elif raw["ended"] and raw["output"] not in ("", "NONE"):
                        if sid in shown:
                            shown[sid] += "\nFollow-up note: " + raw["output"]
                        else:
                            shown[sid] = raw["output"]
                identity = tuple(sorted(shown.items()))
                entry = views.setdefault(identity, {"id": f"{key}/final/{len(views)}", "arms": []})
                entry["arms"].append({"arm": arm, "mode": mode, "reply": reply_id, "selected_card": source})
        for identity, entry in views.items():
            yield entry["id"], name, task["task"], dict(identity), entry["arms"]
    for name in PACKETS:
        task, sources = dossier(name)
        yield f"{name}/pooled", name, task["task"], sources, [{"arm": "solo", "mode": "pooled"}]


def finals(rows):
    for key, _, task, sources, _ in final_views(rows):
        yield previous.prompt(key, 220, FINAL, {"task": task, "delivered_sources": sources})


def episode(generate):
    rows = generate(list(reply_requests()))
    requests = list(finals(rows))
    for start in range(0, len(requests), 8):
        rows.update(generate(requests[start:start + 8]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), Path(previous.__file__), Path(RUNNER.__file__),
             HERE / "facilitator_live_writing_score.py", ROUTING, EVIDENCE / "protocol.md", *PACKETS.values())
    return {str(p.relative_to(ROOT)): RUNNER.digest(p) for p in files}


def verify(directory):
    base = previous.common.reused.previous.prior
    with patch.multiple(base, local=reply_requests, audits=finals, syntheses=lambda rows: (),
                        pins=pins, FAMILY=FAMILY):
        return base.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
