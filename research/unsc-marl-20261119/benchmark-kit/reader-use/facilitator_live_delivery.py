"""Execute frozen third-slot policies through a live English request and reply channel."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_emergency_session as common
import facilitator_third_delivery_action_values as trained

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-live-delivery-evidence"
ACTION_FIT = HERE / "facilitator-third-paired-evidence/action-values.json"
RUNNER = common.reused.runner
ARCHIVE = trained.base.delivery.archive.ARCHIVE
FAMILY = "facilitator-live-delivery"
ARMS = ("learned", "script", "independent")
ROUTE = trained.route
D = trained.delivery
FILES = {"unifil": ARCHIVE / "unifil-final-transfer/verified-transport.json",
         "myanmar": ARCHIVE / "myanmar-sponsorship-probe/score.json"}
TOPICS = {
    "unifil": (
        ("Brazil's assessment of the French text", "How did Brazil assess freedom of movement and the Lebanese concerns that the French draft addressed?"),
        ("China's concerns about sovereignty and consent", "Can you supply Beijing's account of what the text missed and the principles it stressed for peacekeeping?"),
        ("Russia's reason for abstaining", "Please give Moscow's explanation of how the compromise changed before the vote."),
    ),
    "myanmar": (
        ("UK submission and regional consultations", "Who put the draft forward, and which regional counterparts did the sponsor consult?"),
        ("India's national explanation of its abstention", "Please give New Delhi's own rationale for withholding its vote and the diplomatic approach it favored."),
        ("Procedural presidency versus India's national role", "Can you give the sequence of officiating the vote, speaking for the country and returning to the chair?"),
    ),
}
DECODER = (
    "Match the received question to exactly one numbered documentary topic. "
    "Return only its digit. Return 0 for silence. Identify what the question seeks, even if a private desk cannot supply it."
)
PAYLOAD = (
    "Transmit the authorized documentary payload exactly as supplied, including punctuation and any final citation. "
    "Return only that full payload. When the authorized payload is empty, return exactly NONE."
)


def bank(name):
    archived = json.loads(FILES[name].read_text())
    if name == "unifil":
        rows = [{"mask": m, "text": x["answer"], "points": x["release_points"], "strict": x["strict_complete"]}
                for m in range(8) for x in (archived["bank"][f"team-{m}"],)]
    else:
        rows = [{"mask": x["mask"], "text": x["packet"]["answer"], "points": x["points"], "strict": x["complete"]}
                for x in archived["records"]]
    assert [row["mask"] for row in rows] == list(range(8))
    public = rows[0]["text"]
    notes = tuple(rows[1 << i]["text"].removeprefix(public).strip() for i in range(3))
    assert all(row["text"].startswith(public) for row in rows)
    assert all(notes[i] in row["text"] for row in rows for i in range(3) if row["mask"] & (1 << i))
    assert rows[-1]["strict"] and all(not row["strict"] for row in rows[:-1])
    return rows, ("", *notes)


def policies(name, scenario):
    declared, _ = trained.base.cases()[1][name]
    prior = ROUTE.TEST_PRIORS[scenario]
    left, right, opening, _ = trained.base.context(declared, prior)
    parameters = json.loads(ACTION_FIT.read_text())["learned"]
    learned = trained.infer(parameters, declared, (left, right), opening)
    _, _, q, r = D.scripts()
    independent = D.exact_independent(prior, trained.base.terminal(declared))
    assert np.array_equal(independent[0], left) and np.array_equal(independent[1], right)
    return {"learned": learned, "script": (left, right, q, r), "independent": independent}


def episodes():
    for key, name, prior, li, ri, keep_l, keep_r in (
        ("unifil-pair", "unifil", "uniform", 0, 7, True, True),
        ("unifil-complete", "unifil", "uniform", None, None, True, True),
        ("myanmar-available-role", "myanmar", "correlated_duplicates", 2, 4, True, False),
        ("myanmar-missing-role", "myanmar", "correlated_duplicates", 2, 3, True, False),
    ):
        plans = policies(name, prior)
        left, right, chair, reply = plans["learned"]
        if li is None:
            li, ri = next((l, r) for l in range(8) for r in range(8)
                          if (ROUTE.BITS[left[l]] | ROUTE.BITS[right[r]] |
                              ROUTE.BITS[reply[r, right[r], chair[ROUTE.BITS[left[l]] | ROUTE.BITS[right[r]]]]]) == 7)
        m = int(ROUTE.BITS[left[li]] * keep_l | ROUTE.BITS[right[ri]] * keep_r)
        table = {}
        for arm, (_, _, ask, respond) in plans.items():
            q = int(ask[m])
            b = int(right[ri])
            expected = int(respond[ri, b, q])
            table[arm] = {"query": q, "reply": respond[ri, b].tolist(), "typed_sent": expected,
                          "typed_final": int(m | ROUTE.BITS[expected])}
        yield key, name, {"prior": prior, "inventory": [li, ri], "opening_attempts": [int(left[li]), int(right[ri])],
                          "opening_receipts": m, "arms": table}


def numbering(key):
    order = {"unifil-pair": (2, 0, 1), "unifil-complete": (1, 2, 0),
             "myanmar-available-role": (2, 1, 0), "myanmar-missing-role": (0, 2, 1)}[key]
    return (0, *(i + 1 for i in order))


def prompt(key, cap, command, payload):
    return common.reused.previous.prior.prompt(key, cap, command, payload)


def decode_requests():
    for key, name, case in episodes():
        mapping = numbering(key)
        topics = {str(i): TOPICS[name][q - 1][0] for i, q in enumerate(mapping) if q}
        for q in dict.fromkeys(arm["query"] for arm in case["arms"].values()):
            yield prompt(f"{key}/query/{q}", 8, DECODER, {"topics": topics, "question": TOPICS[name][q - 1][1] if q else ""})


def heard(rows, key, q):
    sample = rows[f"{key}/query/{q}"]
    raw = sample["output"]
    return numbering(key)[int(raw)] if sample["ended"] and raw in ("0", "1", "2", "3") else 0


def payload_requests(rows):
    for key, name, case in episodes():
        _, notes = bank(name)
        selected = [a["reply"][heard(rows, key, a["query"])] for a in case["arms"].values()]
        assert all(c == 0 or ROUTE.SEND[case["inventory"][1], c] for c in selected)
        for c in dict.fromkeys(selected):
            yield prompt(f"{key}/payload/{c}", 80, PAYLOAD, {"authorized_payload": notes[c]})


def episode(generate):
    rows = generate(list(decode_requests()))
    rows.update(generate(list(payload_requests(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), Path(trained.__file__), Path(trained.base.__file__), Path(D.__file__),
             Path(RUNNER.__file__), EVIDENCE / "protocol.md", ACTION_FIT,
             HERE / "facilitator_live_delivery_score.py", *FILES.values())
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}


def verify(directory):
    prior = common.reused.previous.prior
    with patch.multiple(prior, local=decode_requests, audits=payload_requests, syntheses=lambda rows: (),
                        pins=pins, FAMILY=FAMILY):
        return prior.read(directory)


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
