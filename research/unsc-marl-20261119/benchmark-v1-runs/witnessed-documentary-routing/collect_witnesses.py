"""Collect exact quote witnesses and check them with the prior native verifier."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
TEMPLATE = RUNS / "reporting-2739/generated-purpose"
READER = RUNS / "claim-scoped-routing"
OUT = HERE / "evidence"
REFORM = RUNS / "reform-2553-transfer/documentary-routing"
AFGHAN = RUNS / "afghanistan-2721-source-contrast/documentary-routing"
sys.path.insert(0, str(TEMPLATE))
import purpose_study as engine

sys.path.insert(0, str(READER))
import collect_claims as scoped

collector = engine.collector
EXTRACT = (
    "Find one contiguous exact quote from the first message that explicitly establishes the claim. "
    "Copy the speaker's own words. Include enough context to make the action, subject and condition "
    "clear, including antecedents if needed, but at most 75 words. A related proposal, consultation, "
    "another person's position, or a general reservation does not establish the exact claim. "
    "If the message does not explicitly establish all of it, return exactly NONE. "
    "Return only the unedited quote or NONE."
)
DELETION = "We would like to be absolutely clear: we will not support his decision without agreement from the de facto authorities."


def read(path):
    return json.loads(path.read_text())


def views():
    output = {}
    for family, path in (("reform", REFORM), ("afghanistan", AFGHAN)):
        archive = read(path / "source-views.json")["views"]
        for key, row in archive.items():
            output[f"{family}/{key}"] = {"family": family, "view": key, "text": row["text"]}
    key = "afghanistan/russia-full"
    text = output[key]["text"]
    assert text.count(DELETION) == 1
    output["afghanistan/russia-agreement-deletion"] = {
        "family": "afghanistan", "view": "russia-agreement-deletion",
        "text": text.replace(" " + DELETION, ""),
    }
    assert len(output) == 13
    return output


def plan():
    origins = (REFORM, AFGHAN)
    paths = (Path(__file__), HERE / "protocol.md", TEMPLATE / "purpose_study.py", TEMPLATE / "plan.json",
             READER / "collect_claims.py", READER / "plan.json",
             *(origin / name for origin in origins for name in ("source-views.json", "plan.json", "results.json")),
             Path(collector.__file__))
    return {
        "pins": {str(p.relative_to(RUNS.parent)): collector.sha(p) for p in paths},
        "checkpoint_index_sha256": collector.sha(collector.MODEL / "model.safetensors.index.json"),
        "extract": EXTRACT, "verify": scoped.SYSTEM, "hypotheses": scoped.HYPOTHESES, "views": views(),
        "labels": {suffix: {letter: "supported" if action == "process" else "unsupported"
                             for letter, action in mapping.items()}
                   for suffix, mapping in scoped.prior.MAPPINGS.items()},
    }


def locked():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    return spec


def exact(reply, source):
    text = reply["text"]
    if text == "NONE" or reply["termination"] != "complete":
        return ""
    outer = {'"': '"', "“": "”"}
    if len(text) > 1 and text[0] in outer and text[-1] == outer[text[0]]:
        text = text[1:-1]
    return text if 0 < len(text.split()) <= 75 and text in source else ""


def episode(call, spec):
    outputs = {}
    for name, row in spec["views"].items():
        hypothesis = spec["hypotheses"][row["family"]]
        answer = call(engine.earlier.request(f"{name}/extract", 115, spec["extract"], {
            "first_message": row["text"], "claim": hypothesis,
        }))
        witness = exact(answer, row["text"])
        verdicts = {}
        if witness:
            for suffix, responses in spec["labels"].items():
                verdicts[suffix] = call(engine.earlier.request(f"{name}/{suffix}", 2, spec["verify"], {
                    "first_message": witness, "claim": hypothesis, "responses": responses,
                }))
        outputs[name] = {"extraction": answer, "exact_span": witness, "verification": verdicts}
    return outputs


def act(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == read(HERE / "plan.json")
    old_run = collector.run

    def track(directory):
        with patch.object(collector, "roster", return_value={"2553-and-2721-documentary-witnesses": {}}):
            return old_run(directory)

    with patch.object(engine, "HERE", HERE), patch.object(engine, "OUT", OUT), patch.object(
        engine, "locked", return_value=spec
    ), patch.object(engine, "episode", episode), patch.object(collector, "run", side_effect=track):
        return {"run": engine.run, "verify": engine.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    args = parser.parse_args()
    result = act(args.mode)
    if args.mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
