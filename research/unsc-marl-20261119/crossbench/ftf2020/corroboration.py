"""Verified two-source record assembly for the August 2020 written ballot."""
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = ("us", "russia", "indonesia_national", "council_president")
PAIRS = tuple(combinations(range(len(KEYS)), 2))
# The prior docket author verified these paraphrases against the two official
# letters. Split the Indonesia roles, and shorten the longer Russia note.
PASSAGES = {
    "us": "In its national explanation, the United States called return to countries of origin or nationality the essential first step. It vetoed S/2020/852 because the draft lacked a reference to repatriation.",
    "russia": "Russia voted in favour to elaborate existing prosecution, rehabilitation and reintegration guidance. It objected that the draft failed to recognize the primary importance of repatriation from Syria and Iraq.",
    "indonesia_national": "In Indonesia's national statement, Dian Triansyah Djani said its draft would guide Member States in developing comprehensive prosecution, rehabilitation and reintegration strategies.",
    "council_president": "Dian Triansyah Djani transmitted the written vote result in his capacity as Council President.",
}
COMPARISON = "Both delegations objected to insufficient recognition of repatriation, despite voting differently."
REQUIRED = {
    "us": {"us"}, "russia": {"russia"}, "indonesia": {"indonesia_national", "council_president"},
    "shared": {"us", "russia"}, "divergent": {"us", "russia"},
}
PROOF = {
    "us": ("the draft lacked a reference to repatriation", "countries of origin or nationality"),
    "russia": ("Russia voted in favour to elaborate existing prosecution, rehabilitation and reintegration guidance",
               "failed to recognize the primary importance of repatriation from Syria and Iraq"),
    "indonesia": ("In Indonesia's national statement", "comprehensive prosecution, rehabilitation and reintegration strategies",
                  "transmitted the written vote result in his capacity as Council President"),
    "shared": ("Both delegations objected to insufficient recognition of repatriation",),
    "divergent": ("despite voting differently", "Russia voted in favour", "The United States cast the only negative vote"),
}


def sha(text):
    return sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def load():
    path = HERE / "task.json"
    task = read(path)
    assert read(HERE / "accession.json")["task_sha256"] == sha256(path.read_bytes()).hexdigest()
    assert set(REQUIRED) == {rule["id"] for rule in task["private_criteria"]}
    sources = {item["id"]: item["text"] for item in task["optional_sources"]}
    assert PASSAGES["us"] == sources["us-explanation"]
    assert PASSAGES["indonesia_national"] in sources["indonesia-explanation"]
    assert "he transmitted the written vote result" in sources["indonesia-explanation"]
    assert "elaborate existing prosecution, rehabilitation and reintegration guidance" in sources["russia-explanation"]
    assert "draft failed to recognize the primary importance of repatriation from Syria and Iraq" in sources["russia-explanation"]
    return task


def packet(index):
    key = KEYS[index]
    return {"key": key, "passage": PASSAGES[key], "sha256": sha(PASSAGES[key])}


def admit(reply, allowed):
    key = reply["key"]
    return (key in allowed and 0 < len(reply["passage"].split()) <= 65
            and reply["sha256"] == sha(PASSAGES[key]) == sha(reply["passage"]))


def compile_record(anchor, reply, allowed):
    assert admit(anchor, KEYS)
    delivered = {anchor["key"]}
    if reply and admit(reply, allowed):
        delivered.add(reply["key"])
    criteria = [key for key, requirement in REQUIRED.items() if requirement <= delivered]
    supplement = " ".join([PASSAGES[key] for key in KEYS if key in delivered]
                          + ([COMPARISON] if "shared" in criteria else []))
    assert len(supplement.split()) <= 85
    final_record = load()["public_record"] + " " + supplement
    proof = {key: list(PROOF[key]) for key in criteria}
    assert all(span in final_record for spans in proof.values() for span in spans)
    return {"admitted_sources": sorted(delivered), "supplement": supplement, "proof": proof,
            "score": 35 + 7 * len(criteria), "supplement_words": len(supplement.split())}


def bank():
    records = {}
    scores = []
    bare = []
    for focus in range(len(KEYS)):
        begin = packet(focus)
        bare.append(compile_record(begin, None, [])["score"])
        rows = []
        for act in range(len(KEYS)):
            candidate = packet(act)
            row = compile_record(begin, candidate, [candidate["key"]])
            records[f"{KEYS[focus]}/{KEYS[act]}"] = row
            rows.append(row["score"])
        scores.append(rows)
    authentic, rejected = 0, 0
    for left, right in PAIRS:
        valid = [KEYS[left], KEYS[right]]
        for i in range(len(KEYS)):
            clean = packet(i)
            assert admit(clean, valid) == (i in (left, right))
            if i in (left, right):
                authentic += 1
            changed = clean["passage"] + " This draft was adopted."
            assert len(changed.split()) <= 65
            corrupt = {**clean, "passage": changed, "sha256": sha(changed)}
            assert not admit(corrupt, valid)
            rejected += 1
    return {"scope": "Original five private criteria and common public record. "
                     "The two Indonesia roles travel as separate source passages. The fixed comparison connects "
                     "only the two admitted explanations. No new model-written records are scored here.",
            "task": load()["id"], "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "task_sha256": sha256((HERE / "task.json").read_bytes()).hexdigest(),
            "keys": KEYS, "fixed_public_record": load()["public_record"], "bare_scores": bare,
            "joint_scores": scores, "records": records, "authentic_allowed_cases": authentic,
            "self_rehashed_corruptions_rejected": rejected}


if __name__ == "__main__":
    print(json.dumps(bank(), indent=2, ensure_ascii=False))
