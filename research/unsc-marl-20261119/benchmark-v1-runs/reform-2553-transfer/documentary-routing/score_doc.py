"""Assemble and score fixed, provenance-checked records for actual native choices."""
import json

from study_doc import CLAIM, HERE, prior, read

case = prior.previous.CASE
all_cards = prior.previous.CARDS
public = [r["id"] for r in case["public"]]
rubric = {r["id"]: r for r in case["rubric"]}
judge = prior.previous.earlier.earlier.previous.load("source_final_judge", prior.previous.RELEASE / "judge_score.py")


def compile_record(key, grounded_cards, action):
    german = {"process": "de-process", "fund": "de-fund"}[action]
    visible = public + grounded_cards + [german]
    evidence = [{"id": id_, "text": all_cards[id_]} for id_ in visible]
    pieces = {item["id"]: (item["text"], [item["id"]]) for item in evidence}
    for relation in case["relations"]:
        if set(relation["needs"]) <= set(visible):
            pieces[relation["id"]] = (relation["text"], relation["needs"])
    answer = "\n\n".join(text for text, _ in pieces.values())
    packet = {"id": key, "mode": "FINAL", "task": case["task"], "rubric": case["rubric"],
              "evidence": evidence, "answer": answer}
    units = []
    for id_ in rubric:
        text, source_ids = pieces.get(id_, ("", []))
        units.append({"id": id_, "status": "met" if text else "unmet", "response": text,
                      "source": [{"block": k, "quote": all_cards[k]} for k in source_ids],
                      "reason": "The preserved source text establishes this criterion." if text
                      else "No qualifying claim was included."})
    verdict = {"id": key, "units": units, "guard": {
        "status": "clear", "response": "", "source": [],
        "reason": "The renderer includes only reviewed, visible national and public facts, and approved pair clauses.",
    }}
    score = judge.score(packet, verdict)
    words = len(answer.split())
    assert words <= case["word_cap"]
    assert score["guard"] == "clear"
    return {"released_70": score["final"]["lower"], "words": words,
            "packet": packet, "verdict": verdict}


def margins(data, arm, view):
    mapped = {}
    for suffix, labels in prior.MAPPINGS.items():
        scores = data[f"{arm}/{view}/{suffix}"]["logits"]
        process = next(label for label, role in labels.items() if role == "process")
        fund = next(label for label, role in labels.items() if role == "fund")
        mapped[suffix] = scores[process] - scores[fund]
    return mapped | {"mean": sum(mapped.values()) / len(mapped)}


def run():
    verified = read(HERE / "verified.json")["outputs"]
    documentary = read(HERE / "source-views.json")
    claims = read(CLAIM / "results.json")["reform_claim_scoped"]["coefficients"]
    direct = read(CLAIM.parent / "reform-2553-transfer/text-reply-transfer/results.json")["coefficients"]
    outputs = {}
    for view, doc in documentary["views"].items():
        banks = {option: compile_record(f"{view}/{option}", doc["verified_cards"], option)
                 for option in ("process", "fund")}
        choices = {"fixed_fund": "fund", "fixed_process": "process"}
        scores = {}
        for arm, coefs in (("direct", direct), ("claim", claims)):
            scores[arm] = margins(verified, arm, view)
            m = scores[arm]["mean"]
            choices[f"{arm}_mean"] = "process" if m > 0 else "fund"
            choices[f"{arm}_fitted"] = "process" if coefs[0] + coefs[1] * m > 0 else "fund"
        choices["oracle"] = max(banks, key=lambda opt: banks[opt]["released_70"])
        assert banks["process"]["released_70"] != banks["fund"]["released_70"]
        outputs[view] = {"source_page": doc["page"], "grounded_card_ids": doc["verified_cards"],
                         "marks": scores, "choices": {
                             key: {"action": action, "released_70": banks[action]["released_70"],
                                   "compiled_record": f"{view}/{action}"}
                             for key, action in choices.items()},
                         "records": banks}
    metrics = {}
    for arm in next(iter(outputs.values()))["choices"]:
        total = sum(row["choices"][arm]["released_70"] for row in outputs.values())
        metrics[arm] = {"mean_release": round(total / len(outputs), 8),
                        "oracle_matches": sum(row["choices"][arm]["action"] == row["choices"]["oracle"]["action"]
                                              for row in outputs.values())}
    return {"source_sha256": documentary["pdf_sha256"], "cases": outputs, "summary": metrics}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
