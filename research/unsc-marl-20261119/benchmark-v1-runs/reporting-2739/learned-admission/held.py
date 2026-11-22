"""Freeze role-local scope probes and collect paired native Qwen margins."""
import argparse
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
import sys
from unittest.mock import patch
import json

import team

HERE, OUT = team.HERE, team.HERE / "evidence"
sys.path.append(str(team.REL))
import facilitator_source_relation as archived

spec = spec_from_file_location("reporting_transfer_base", HERE.parent / "collect.py")
report = module_from_spec(spec)
spec.loader.exec_module(report)
e, base, suite, CASE = report.e, report.base, report.suite, report.CASE
BLOCK = e.judge.by_id(e.evidence(CASE))

REPORTING = "It continued to value the Secretary-General’s monthly reports on attacks on merchant and commercial vessels for keeping the Council informed."
SPONSORS = "Speaking for the United States and Japan after the vote, Mr. Wood explained that extending the Secretary-General’s reporting would provide the Council with accurate and timely information for future deliberations on the Houthi attacks."
ALGERIA_VOTE = "Algeria, China and the Russian Federation abstained."
SPONSORS_VOTE = "Both co-sponsors voted in favour."
SPECS = (
    ("algeria-reporting", "supports", "algeria", REPORTING,
     "Algeria valued continued monthly shipping-attack reports for keeping the Council informed."),
    ("algeria-deadline-endorsement", "unknown", "algeria", REPORTING,
     "Algeria endorsed the extension of reporting through 15 January 2025."),
    ("algeria-cessation-opposition", "unknown", "algeria", REPORTING,
     "Algeria opposed the Council's demand that the Houthis cease their attacks."),
    ("algeria-affirmative-vote", "contradicts", "vote", ALGERIA_VOTE,
     "Algeria voted in favour of adopting resolution 2739 (2024)."),
    ("sponsors-informed-deliberation", "supports", "sponsors", SPONSORS,
     "The United States and Japan said continued reporting would give the Council accurate, timely information for future deliberations."),
    ("sponsors-exclusive-purpose", "unknown", "sponsors", SPONSORS,
     "The United States and Japan said information gathering was the sole purpose of the resolution."),
    ("sponsors-authorization-position", "unknown", "sponsors", SPONSORS,
     "The United States and Japan explicitly said they held no position on authorization of military action."),
    ("sponsors-abstentions", "contradicts", "sponsors", SPONSORS_VOTE,
     "Japan and the United States abstained on the vote on resolution 2739 (2024)."),
)


def fixtures():
    return [{"id": key, "expected": gold, "source": block, "witness": quote, "assertion": claim}
            for key, gold, block, quote, claim in SPECS]


def asks():
    for row in fixtures():
        source = BLOCK[row["source"]]["text"]
        assert source.count(row["witness"]) == 1
        payload = {"quoted_premise": row["witness"], "passage_for_references": source,
                   "assertion": row["assertion"]}
        for item in archived.protocol.encoded(("held", row["id"]), archived.TASK, payload, archived.OPTIONS):
            yield item | {"observation": list(item["observation"]), "legal": list(item["legal"]),
                          "max_output_tokens": 2}


def plan():
    files = (Path(__file__), Path(team.__file__), HERE / "protocol.md", HERE / "fit.json",
             HERE / "held.json", Path(archived.__file__), Path(archived.protocol.__file__),
             Path(base.__file__), HERE.parent / "docket.json", report.RELEASE / "release.json")
    return {"requests": list(asks()), "physical_calls": 16,
            "sha256": {str(path.relative_to(team.STUDY)): team.pin(path) for path in files}}


def lock():
    assert fixtures() == team.read(HERE / "held.json")
    assert plan() == team.read(HERE / "plan.json")


def ids(tok):
    values = [tok.encode(letter, add_special_tokens=False) for letter in "ABC"]
    assert all(len(v) == 1 for v in values)
    result = [v[0] for v in values]
    assert len(set(result)) == 3
    return result


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    lock()
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    labels = ids(tok)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    state = {}

    def select(model, *args, **kwargs):
        prefix = kwargs["input_ids"]
        assert prefix[0].tolist() == base.prompt(tok, state["request"])
        full = model(input_ids=prefix, attention_mask=kwargs["attention_mask"],
                     use_cache=False, logits_to_keep=1).logits[0, -1].float()
        legal = full[labels]
        state["scores"] = legal.tolist()
        state["legal_mass"] = float((legal.logsumexp(0) - full.logsumexp(0)).exp())
        suffix = torch.tensor([[labels[int(legal.argmax())], eos]], device=prefix.device, dtype=prefix.dtype)
        return torch.cat((prefix, suffix), dim=-1)

    def collect(generate, directory):
        for item in asks():
            state["request"] = item
            reply = generate(item)
            row = item | {"reply": reply, "scores": state.pop("scores"), "legal_mass": state.pop("legal_mass")}
            suite.append(directory / "calls.jsonl", row)

    with patch.object(GenerationMixin, "generate", select), patch.object(
        suite, "collect", collect
    ), patch.object(base, "HERE", HERE), patch.object(base, "roster", return_value={CASE["id"]: CASE}):
        base.run(OUT)


def lines(name):
    return [json.loads(line) for line in (OUT / name).read_text().splitlines()]


def verify():
    from transformers import AutoTokenizer

    lock()
    manifest = team.read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "tokens.jsonl", "launch.json"}
    assert all(team.pin(OUT / name) == digest for name, digest in manifest.items())
    receipt = team.read(OUT / "launch.json")
    assert receipt["optimizer_updates"] == 0 and receipt["cases"] == [CASE["id"]]
    assert receipt["protocol_sha256"] == team.pin(HERE / "protocol.md")
    assert receipt["release_sha256"] == team.pin(report.RELEASE / "release.json")
    assert receipt["collector_sha256"] == team.pin(Path(base.__file__))
    assert receipt["checkpoint_index_sha256"] == report.plan()["checkpoint_index_sha256"]
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    labels, eos = ids(tok), tok.convert_tokens_to_ids("<|im_end|>")
    checks = []
    for item, actual, trace in zip(asks(), lines("calls.jsonl"), lines("tokens.jsonl"), strict=True):
        assert all(actual[k] == v for k, v in item.items())
        assert trace["input_ids"] == base.prompt(tok, item)
        assert trace["response"] == actual["reply"]
        assert len(trace["input_ids"]) == actual["reply"]["input_tokens"]
        assert 0 <= actual["legal_mass"] <= 1
        pick = max(range(3), key=actual["scores"].__getitem__)
        assert trace["output_ids"] == [labels[pick], eos] and actual["reply"]["text"] == "ABC"[pick]
        checks.append({"observation": item["observation"], "scores": actual["scores"],
                       "input_tokens": len(trace["input_ids"]), "output_tokens": len(trace["output_ids"])})
    assert len(checks) == 16
    return {"records": checks, "evidence_sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fixtures", "plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"fixtures": fixtures, "plan": plan, "verify": verify}[mode]())
