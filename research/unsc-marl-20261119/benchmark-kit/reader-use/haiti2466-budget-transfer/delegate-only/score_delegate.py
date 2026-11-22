"""Score matched delegation-only bodies and check their requested line labels."""
import argparse
from hashlib import sha256
import json

from run_delegate import EVIDENCE, FAMILY, HERE, base, pins, requests
from score_transfer import assess, read_rows, verify_generation


def masked(key):
    return sha256(("2466-delegate-only/" + key).encode()).hexdigest()[:10]


def score(rows):
    expected = requests()
    original, mapping = base.prompts()
    previous = {r["id"]: r for r in original}
    for request in expected:
        match = previous[request["id"]]
        assert request["messages"][1:] == match["messages"][1:] and request["cap"] == match["cap"]
    verify_generation(EVIDENCE, rows, expected, FAMILY, pins())
    marks = base.read(HERE / "marks.json")
    assert marks.keys() == {masked(k) for k in rows} and len(rows) == 2
    results = {}
    packet = base.read(base.PACKET)
    for key, row in rows.items():
        result = assess(row, marks[masked(key)], mapping["catalog"][key], packet)
        evidence = json.loads(row["messages"][1]["content"])
        required = [n["desk"] for n in evidence]
        lines = [line for line in row["output"].splitlines() if line.strip()]
        result["line_labels_match"] = (
            len(lines) == len(required) and all(line.startswith(f"{name}:") for line,name in zip(lines, required))
        )
        results[key] = result
    return {"verified_outputs": len(rows), "records": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "score", "records"))
    mode = cli.parse_args().mode
    rows = read_rows(EVIDENCE)
    if mode == "score":
        result = score(rows)
    elif mode == "deck":
        result = dict(sorted((masked(k), r["output"]) for k, r in rows.items()))
    else:
        result = {k: base.read(base.PACKET)["public"] + "\n\n" + r["output"] for k, r in rows.items()}
    print(json.dumps(result,ensure_ascii=False,indent=2))
