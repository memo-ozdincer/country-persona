"""Check selection answers against exact candidate IDs before forwarding clauses."""
import argparse
import json
import re
import sys

from run_delivery import EVIDENCE, FAMILY, HERE, base, cases, pins, requests
sys.path.insert(0, str(HERE.parent.parent / "bosnia2604-routing/protected-record"))
from score_protected import read_rows, verify_generation

FORMATS = {
    "numbered": re.compile(r"1=([A-Z][0-9]+|EMPTY)\n2=([A-Z][0-9]+|EMPTY)"),
    "bare": re.compile(r"([A-Z][0-9]+|EMPTY)\n([A-Z][0-9]+|EMPTY)"),
    "identity": re.compile(r"([A-Z][0-9]+|EMPTY)\n([A-Z][0-9]+|EMPTY)"),
}


def decode(text, expected, offered, ended=True, grammar="numbered"):
    parsed = FORMATS[grammar].fullmatch(text)
    if not ended or parsed is None:
        return None, [False, False]
    values = list(parsed.groups())
    if grammar == "identity":
        accepted = [key != "EMPTY" and key in offered and key in values for key in expected]
    else:
        accepted = [x == y and x != "EMPTY" and x in offered for x, y in zip(values, expected, strict=True)]
    return values, accepted


def controls(grammar):
    expected, offered = ["M7", "P2"], {"M7", "P2", "X4"}
    probes = (
        ("correct", "1=M7\n2=P2", expected, offered, True, [True, True]),
        ("swapped", "1=P2\n2=M7", expected, offered, True, [False, False]),
        ("wrong-field", "1=X4\n2=P2", expected, offered, True, [False, True]),
        ("unknown-id", "1=Z9\n2=P2", expected, offered, True, [False, True]),
        ("same-id", "1=M7\n2=M7", expected, offered, True, [True, False]),
        ("excess-text", "1=M7\n2=P2\nBoth supported", expected, offered, True, [False, False]),
        ("truncated", "1=M7\n2=P2", expected, offered, False, [False, False]),
        ("withheld-hallucination", "1=M7\n2=P2", ["M7", "EMPTY"], {"M7", "X4"}, True, [True, False]),
    )
    result = {}
    for name, raw, fields, choices, end, wanted in probes:
        if grammar in {"bare", "identity"}:
            raw = raw.removeprefix("1=").replace("\n2=", "\n", 1)
        _, actual = decode(raw, fields, choices, end, grammar)
        if grammar == "identity" and name == "swapped":
            wanted = [True, True]
        assert actual == wanted
        result[name] = actual
    example = "1=P2\n2=EMPTY" if grammar == "numbered" else "P2\nEMPTY"
    _, last = decode(example, ["EMPTY", "P2"], {"P2", "X4"}, True, grammar)
    assert last == [False, grammar == "identity"]
    result["survivor_shifted_to_missing_field"] = last
    return result


def score(rows, grammar):
    verify_generation(EVIDENCE, rows, requests(), FAMILY, pins())
    assert len(rows) == 15
    observed = [[0] * 4 for _ in range(4)]
    packet = base.read(base.PACKET)
    reports = {}
    for request, expected in cases():
        key = request["id"]
        category, source = key.split("/")
        source = int(source)
        row = rows[key]
        offered = json.loads(request["messages"][1]["content"])["candidate_passages"]
        values, okay = decode(row["output"], expected, offered, row["ended"], grammar)
        fields = packet["cards"][source - 1]["atoms"]
        admitted = [field["id"] for field, accepted in zip(fields, okay, strict=True) if accepted]
        mask = sum(1 << (2 * (source - 1) + i) for i, true in enumerate(okay) if true)
        if category != "withheld":
            observed[int(category)][source] = mask
        reports[key] = {"output": row["output"], "expected": expected, "parse": values,
                        "accepted": admitted, "fully_correct": values == expected,
                        "withheld_safely": all(not passed for passed, wanted in zip(okay, expected, strict=True)
                                               if wanted == "EMPTY"),
                        "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    assert all(r["withheld_safely"] for r in reports.values())
    return {"grammar": grammar, "admitted_masks": observed, "reports": reports,
            "software_controls": controls(grammar)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grammar", choices=FORMATS)
    print(json.dumps(score(read_rows(EVIDENCE), parser.parse_args().grammar), ensure_ascii=False, indent=2))
