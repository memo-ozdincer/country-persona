"""Score repaired missing-field outputs against the unchanged ownership gate."""
import json

from run_slots import EVIDENCE, FAMILY, HERE, pins, prev, requests
from admission import decode, read_rows, verify_generation


def score():
    expected = {r["id"]: (r, pair) for r, pair in prev.cases() if r["id"].startswith("withheld/")}
    rows = read_rows(EVIDENCE)
    verify_generation(EVIDENCE, rows, requests(), FAMILY, pins())
    assert set(expected) == rows.keys() and len(rows) == 3
    original = prev.base.read(HERE.parent / "bare-admission.json")["reports"]
    packet = prev.base.read(prev.base.PACKET)
    result = {}
    for key, row in rows.items():
        req, pair = expected[key]
        assert req["messages"][1:] == row["messages"][1:]
        offered = json.loads(req["messages"][1]["content"])["candidate_passages"]
        selected, allowed = decode(row["output"], pair, offered, row["ended"], "bare")
        source = int(key.rsplit("/", 1)[1])
        delivered = [a["id"] for a, good in zip(packet["cards"][source - 1]["atoms"], allowed, strict=True) if good]
        absent = pair.index("EMPTY")
        assert not allowed[absent]
        result[key] = {"old": original[key]["output"], "repaired": row["output"], "expected": pair,
                       "old_admitted": original[key]["accepted"], "admitted": delivered,
                       "admitted_mask": sum(1 << (2 * (source - 1) + i) for i, ok in enumerate(allowed) if ok),
                       "abstained_in_right_slot": bool(selected is not None and selected[absent] == "EMPTY"),
                       "fully_correct": selected == pair, "input_tokens": len(row["input_ids"]),
                       "output_tokens": len(row["output_ids"])}
    return {"verified_prompt_interventions": len(rows), "cases": result}


if __name__ == "__main__":
    print(json.dumps(score(), ensure_ascii=False, indent=2))
