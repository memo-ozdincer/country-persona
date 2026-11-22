"""Source-blind extraction with verbatim candidate windows and offline scoring."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from unittest.mock import patch

import judge as prior

# The query retrieves candidate text only. Each menu describes possible
# candidate claims, with the archival value used solely by the local scorer.
FIELDS = {
    "vote": (r"resolution 2682|S/2023/378", "How does the record identify the draft that became resolution 2682?", (
        "It says the Council adopted resolution 2682 and gives the US draft and symbol S/2023/378.",
        "It identifies the adoption but omits the draft symbol or the sponsor.",
        "It gives an incompatible disposition, draft identity, or sponsor.")),
    "tally": (r"15 in favour|unanim|explanation of vote", "What does the record say about the final vote and national voting explanations?", (
        "It gives the affirmative unanimous vote and says no national explanation appears in this meeting record.",
        "It gives only the tally or only the absence of explanations.",
        "It gives an incompatible tally or reports a national explanation during this meeting.")),
    "term": (r"mandate (?:was |be )?(?:extended|renewed|until|through)|extended the .*?mandate", "Which action and expiry date does the record give for the existing UNAMI mandate?", (
        "It extends the existing mandate until 31 May 2024.",
        "It omits the action or expiry date for the mandate.",
        "It gives a different expiry date or says the mandate was terminated.")),
    "support": (r"dialogue|reconciliation", "How does the record qualify UNAMI assistance for dialogue or reconciliation?", (
        "It says the assistance or advice is at the request of the Government of Iraq.",
        "It mentions the activity without saying the Iraqi Government requested it.",
        "It expressly says the activity does not require an Iraqi request or is imposed against Iraq's request.")),
    "participation": (r"participation|youth input|civil.society.*?input", "Which participation standard and input requirement does the record state?", (
        "It gives meaningful participation to women and treats civil society and youth as sources of input.",
        "It gives only one requirement or merely names the groups.",
        "It explicitly applies the same full, equal and meaningful participation standard to women, civil society and youth.")),
    "deliverable": (r"strategic review|submit (?:it|the review)|provide (?:it|the review)", "Who is to deliver what to whom, and when, according to the record?", (
        "It says the Secretary-General is to conduct and submit the independent strategic review to the Council by 31 March 2024.",
        "It gives only part of that deliverable, leaving the actor, recipient or deadline unstated.",
        "It gives a conflicting review deadline, recipient or actor.")),
    "consult": (r"consult", "Which entities does the record explicitly include among the review's consultees?", (
        "It lists Iraq and Kuwait and at least one multilateral or non-state category.",
        "It lists only some of these required consultees.",
        "It explicitly excludes a required consultee from the review.")),
    "recommend": (r"relevance|recommend|assess.*?(?:mandate|threats)|evaluat", "What does the record say the review is to do with UNAMI's tasks and possible changes?", (
        "It says the review assesses relevance and gives recommendations about mandate, structure or staffing.",
        "It mentions assessment or evaluation without giving both relevance and recommendations.",
        "It says the review implements changes or itself revises the mandate.")),
    "regional": (r"regional cooperation|^.*\band ways\s*$", "What does the record say the review will assess regarding regional cooperation?", (
        "It states that the review assesses ways to help Iraq strengthen regional cooperation.",
        "It just names regional cooperation, leaves Iraq out, or stops before describing the assessment.",
        "It states that the review imposes an operative regional cooperation requirement or explicitly excludes it.")),
    "report": (r"four months|reporting cycle", "What separate reporting cycle does the record give for the Secretary-General?", (
        "It distinguishes recurring reports every four months from the strategic review.",
        "It fails to specify separate recurring reports every four months.",
        "It states a different interval, or describes the cycle as repeated strategic reviews.")),
}
STATUS = ("supported", "omitted", "contradicted")
ORDERS = ((0, 1, 2), (2, 0, 1))


def windows(candidate, field):
    query = re.compile(FIELDS[field][0], re.I)
    return tuple((m.start(), m.end(), m.group()) for m in re.finditer(r"\S.*?(?:(?<=[.!?])\s+(?=[A-Z])|\Z)",
                 candidate, re.S) if query.search(m.group()))


def cases():
    for key, candidate, truth in prior.fixtures():
        yield key, candidate, truth
    controls = (
        ("review-recipient", "to the Council by 31 March 2024", "to the Government of Iraq by 31 March 2024", "deliverable"),
        ("participation-promotion", "women's meaningful participation and civil-society and youth input",
         "full, equal and meaningful participation of women, civil society and youth", "participation"),
        ("consult-explicit-exclusion", "Iraq, Kuwait and civil society", "Iraq and civil society, explicitly excluding Kuwait", "consult"),
        ("false-reporting-cycle", "every four months", "every six months", "report"),
    )
    for name, old, new, field in controls:
        assert prior.RECORD.count(old) == 1
        yield (name, field), prior.RECORD.replace(old, new), "contradicted"


def observations():
    for (name, field), candidate, _ in cases():
        excerpts = windows(candidate, field)
        if not excerpts:
            continue
        _, task, options = FIELDS[field]
        for i, order in enumerate(ORDERS):
            body = {"field": task, "candidate_excerpts": [text for _, _, text in excerpts],
                    "choices": dict(zip("ABC", (options[j] for j in order), strict=True))}
            yield {"observation": (name, field, i), "legal": order, "messages": [
                {"role": "system", "content": "Read only the quoted candidate excerpts. Select what the writer explicitly "
                 "asserts, even when factually false. Do not supply missing details from another document or world knowledge. "
                 "Require every component of the selected description. A passing mention or an unfinished sentence can leave "
                 "a fact unstated. Reply with one choice letter."},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)}]}


def locks():
    files = [Path(__file__).resolve(), Path(prior.__file__), prior.PACK, prior.FINAL_TEXT,
             Path(prior.relay_text.__file__)]
    return {f.name: prior.runner.digest(f) for f in files}


def report(directory):
    reviewer, _ = prior.reviewed()
    with patch.multiple(prior.relay_text, observations=observations, hashes=locks):
        measured = prior.relay_text.read(directory)
    results = {"authored": [], "generated": []}
    for (name, field), candidate, truth in cases():
        group = "authored" if truth else "generated"
        truth = truth or reviewer[name, field]
        found = windows(candidate, field)
        assert all(text == candidate[start:end] for start, end, text in found)
        votes = []
        for i, order in enumerate(ORDERS):
            if not found:
                break
            logits = measured[name, field, i]["scores"]
            best = [STATUS[j] for j, value in zip(order, logits, strict=True) if value == max(logits)]
            votes.append(best[0] if len(best) == 1 else None)
        verdict = votes[0] if votes and len(set(votes)) == 1 else None
        # An absent retrieval is a review referral. It cannot grant points
        # or prove omission from the full record.
        results[group].append({"candidate": name, "field": field, "reference": truth,
                               "windows": found, "orders": votes, "verdict": verdict})
    return {"scope": "Case-specific source-blind field extraction on an exposed docket. "
                     "Exact windows establish provenance. Semantic labels still require validation.",
            "groups": {name: {"n": len(rows), "correct": sum(x["verdict"] == x["reference"] for x in rows),
                              "deferred": sum(x["verdict"] is None for x in rows),
                              "by_reference": Counter(x["reference"] for x in rows), "records": rows}
                       for name, rows in results.items()}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "report", "check"))
    cli.add_argument("directory", nargs="?", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(prior.relay_text, observations=observations, hashes=locks):
            prior.relay_text.score(args.model, args.directory)
    elif args.mode == "report":
        print(json.dumps(report(args.directory), indent=2, ensure_ascii=False))
    else:
        keys = [(name, field) for (name, field), _, _ in cases()]
        assert len(keys) == len(set(keys)) == 54
        print({"case_fields": len(keys), "judge_calls": len(list(observations()))})
