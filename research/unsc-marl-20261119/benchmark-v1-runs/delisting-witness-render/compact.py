"""Replay compact comparison links while retaining exact witness offsets."""
import json
from unittest.mock import patch

import witness

HERE = witness.HERE
scoring = witness.scoring
read = scoring.read
APOSTROPHES = str.maketrans({"‘": "'", "’": "'"})


def compact(reply, sources):
    # The source normalization is length-preserving, so the offsets still
    # locate the exact original text. Formatting and source checks are
    # unchanged except for this typography and the removed display budget.
    normalized_sources = {key: text.translate(APOSTROPHES) for key, text in sources.items()}
    normalized_reply = reply | {"text": reply["text"].translate(APOSTROPHES)}
    obj, failure = witness.spans(normalized_reply, normalized_sources)
    if failure not in {None, "quote_budget"}:
        return {"text": "NONE", "witnesses": {}, "fallback": failure}
    if failure == "quote_budget":
        # The existing validator reaches the budget check only after
        # validating the schema, distinct spans and source membership.
        obj = json.loads(normalized_reply["text"])
    evidence = {}
    for owner, field in (("delegate", "delegate_statement"), ("document", "adopted_document")):
        evidence[field] = []
        for text in obj[owner]:
            start = normalized_sources[field].index(text)
            stop = start + len(text)
            evidence[field].append({"start": start, "end": stop, "quote": sources[field][start:stop]})
    return {"text": witness.CONNECTIVES[obj["type"]], "witnesses": evidence, "fallback": None}


def run(score=False):
    spec = witness.plan()
    assert spec == read(HERE / "plan.json")
    verified = read(HERE / "verified.json")
    results = {
        key: compact(reply, json.loads(spec["requests"][key]["messages"][1]["content"]))
        for key, reply in verified["outputs"].items()
    }
    if not score:
        return results
    real = read(witness.PRIOR / "plan.json")["requests"]
    projected = spec | {"requests": {key: spec["requests"][key] for key in real}}
    outputs = {key: verified["outputs"][key] | {"text": results[key]["text"]} for key in real}

    def read_for_score(path):
        if path == HERE / "plan.json":
            return projected
        if path == HERE / "verified.json":
            return verified | {"outputs": outputs}
        if path == HERE / "marks.json":
            return read(HERE / "compact-marks.json")
        return read(path)

    with patch.object(scoring, "HERE", HERE), patch.object(scoring, "plan", return_value=projected), patch.object(
        scoring, "read", side_effect=read_for_score
    ):
        evaluated = scoring.run()
    return evaluated | {"renderings": results, "control_marks": read(HERE / "compact-control-marks.json")}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", action="store_true")
    print(json.dumps(run(parser.parse_args().score), ensure_ascii=False, indent=2))
