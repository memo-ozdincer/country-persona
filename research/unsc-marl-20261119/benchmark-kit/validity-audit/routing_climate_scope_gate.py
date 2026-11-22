"""Calibrate an automatic Sahel-alternative scope check on actual receipts and contrasts."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import peer_evidence_affirmative as affirmative
import routing_climate_scope as followup

transfer, read, digest, runner = followup.transfer, followup.read, followup.digest, followup.runner
MAIN = followup.BASE
FOLLOW = MAIN.parent / "climate2021-scope-writer"
MODEL = MAIN / "launch.json"
EXTRACTION_QUESTIONS = (
    "Does the sentence restrict the proposal's policy scope to climate-related problems, apart from its geographic scope?",
    "Does the sentence state that the proposal deals exclusively with climate-related drivers or effects?",
)
EXTRACTION_SYSTEM = (
    "Read only the candidate sentence. Determine what it asserts about the proposal's subject matter. "
    "A geographic limit and a substantive restriction are different. Mentioning climate or drought alongside "
    "other causes is different from restricting the whole proposal to climate-related matters. Resolve what "
    "any word such as 'only' or 'limited' modifies. Output YES or NO."
)
SENTENCE = re.compile(r"[^.!?]+[.!?]?")
PROPOSAL = re.compile(r"\b(?:alternative|draft|proposal|approach)\b", re.I)


def sentences(text):
    return [match.group().strip() for match in SENTENCE.finditer(text) if match.group().strip()]


def candidate_scope_sentence(text):
    choices = [s for s in sentences(text) if PROPOSAL.search(s) and "sahel" in s.lower()]
    return choices[0] if choices else None


def selected_cases():
    original = {row["id"]: row for row in transfer.captured(MAIN, MAIN / "plan.json")}
    revised = {row["id"]: row for row in followup.captured(FOLLOW)}
    fixture = transfer.task()
    india = next(row["text"] for row in fixture["optional_sources"] if row["id"] == "india-explanation")
    combined = india + " " + next(row["text"] for row in fixture["optional_sources"]
                                   if row["id"] == "russia-explanation")
    edit = read(FOLLOW / "source-edit.json")["alternatives"]["verified_scope_replacement"]["edited_supplement"]
    return [
        ("actual-offending", candidate_scope_sentence(original["visible-2"]["output"]), india, True),
        ("actual-reprompted", candidate_scope_sentence(revised["visible-2"]["output"]), india, True),
        ("actual-reviewed-repair", candidate_scope_sentence(edit), india, False),
        ("actual-two-source", candidate_scope_sentence(original["visible-3"]["output"]), combined, False),
        ("safe-geography-only", "India backed a security proposal limited to the Sahel region.", india, False),
        ("safe-climate-among-factors", "The Sahel alternative addressed regional security, with climate pressures among several relevant factors.", combined, False),
        ("safe-only-modifies-region", "Only the Sahel was in the alternative draft's geographic scope, and security drivers included climate risks.", combined, False),
        ("safe-includes-climate", "India backed a Sahel-specific security proposal that included climate pressures.", india, False),
        ("bad-only-modifies-policy", "India backed a Sahel proposal concerning only the security effects of climate change.", india, True),
        ("bad-climate-only-paraphrase", "The alternative draft for the Sahel dealt exclusively with insecurity driven by the changing climate.", combined, True),
        ("bad-drought-only", "The Russian and Indian Sahel alternative would consider drought alone as a source of insecurity.", combined, True),
        ("bad-explicit-exclusion", "The alternative draft limited to the Sahel addressed climate pressures and excluded other causes of conflict.", combined, True),
    ]


def requests():
    for key, claim, evidence, _ in selected_cases():
        assert claim and "Sahel" in claim
        for i, question in enumerate(affirmative.QUESTIONS):
            yield affirmative.make_request(f"{key}/support-{i}", claim, evidence, question)
        for i, question in enumerate(EXTRACTION_QUESTIONS):
            body = {"candidate_sentence": claim, "question": question}
            yield {"id": f"{key}/restriction-{i}", "cap": 4, "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
            ]}


def locks():
    paths = (Path(__file__), Path(affirmative.__file__), Path(runner.__file__), transfer.TASK, MAIN / "transcript.jsonl",
             FOLLOW / "transcript.jsonl", FOLLOW / "source-edit.json", MODEL)
    return {str(p.relative_to(transfer.base.space.ROOT)): digest(p) for p in paths}


def episode(generate):
    plans = list(requests())
    results = {}
    for start in range(0, len(plans), 12):
        results.update(generate(plans[start:start + 12]))
    return [{"family": "climate-scope-gate", "final": results}]


def run(directory):
    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(Path(read(MODEL)["model"]), directory)


def score(directory):
    assert read(directory / "launch.json")["sha256"] == locks()
    complete = read(directory / "complete.json")
    raw, final = directory / "transcript.jsonl", directory / "final-records.json"
    assert digest(raw) == complete["transcript_sha256"] and digest(final) == complete["final_records_sha256"]
    rows = list(map(json.loads, raw.read_text().splitlines()))
    assert len(rows) == complete["records"]
    for row, req in zip(rows, requests(), strict=True):
        assert all(row[key] == value for key, value in req.items())
    outputs = {row["id"]: row["output"] for row in rows}
    assert read(final)["climate-scope-gate"] == outputs
    records = []
    for key, claim, _, expected in selected_cases():
        replies = {mode: [outputs[f"{key}/{mode}-{i}"] for i in range(2)]
                   for mode in ("support", "restriction")}
        binary = {mode: [affirmative.factored.normalized(out, 0) for out in preds] for mode, preds in replies.items()}
        outcomes = {name: (votes[0] if votes[0] == votes[1] else None) for name, votes in binary.items()}
        outcomes["support"] = None if outcomes["support"] is None else not outcomes["support"]
        records.append({"key": key, "claim": claim, "unsupported_restriction": expected,
                        "raw": replies, "model_blocks_by_method": outcomes})
    counts = {}
    for mode in ("support", "restriction"):
        hit = [x for x in records if x["model_blocks_by_method"][mode] == x["unsupported_restriction"]]
        counts[mode] = {
            "correct": len(hit),
            "false_acceptances": sum(x["unsupported_restriction"] and x["model_blocks_by_method"][mode] is False for x in records),
            "false_rejections": sum(not x["unsupported_restriction"] and x["model_blocks_by_method"][mode] is True for x in records),
            "uncertain": sum(x["model_blocks_by_method"][mode] is None for x in records),
        }
    return {"scope": "Targeted retrospective scope gate. Human-authored contrast labels. The document map supplies "
                     "the proposition that the alternative is region-specific and its restriction to climate-only "
                     "security claims is unsupported. Extraction examines what the candidate asserts without showing "
                     "it the source. This is calibrated on exposed cases and synthetic contrasts.",
            "summary": counts, "items": records, "trace_sha256": digest(raw)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("path", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "run":
        run(args.path)
    elif args.mode == "score":
        print(json.dumps(score(args.path), indent=2, ensure_ascii=False))
    else:
        cases = selected_cases()
        plans = list(requests())
        assert len(plans) == len({p["id"] for p in plans}) == 48
        print(json.dumps({"cases": len(cases), "calls": len(plans), "locks": locks()}, indent=2))
