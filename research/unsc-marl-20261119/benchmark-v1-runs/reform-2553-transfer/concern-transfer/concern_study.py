"""Collect a prompted shared-concern payload under genuine source-card contrasts."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1]
PRIOR = RUNS / "reporting-2739/generated-purpose"
OUT = HERE / "evidence"
sys.path.insert(0, str(PRIOR))
import purpose_study as earlier

collector = earlier.collector
RELEASE = earlier.previous.base.RELEASE
CASE = json.loads((HERE.parent / "docket.json").read_text())
CARDS = {card["id"]: card["text"] for card in CASE["public"] + [
    card for group in CASE["owned"] for card in group
]}
OWNERS = {"gb-process": "the UK", "de-process": "Germany", "de-fund": "Germany", "be-funding": "Belgium"}
VIEWS = {
    "process-uk-first": ("gb-process", "de-process"),
    "process-germany-first": ("de-process", "gb-process"),
    "cross-uk-first": ("gb-process", "de-fund"),
    "cross-germany-first": ("de-fund", "gb-process"),
    "fund-germany-first": ("de-fund", "be-funding"),
    "fund-belgium-first": ("be-funding", "de-fund"),
    "uk-only": ("gb-process",),
}
SOURCE_PROMPT = earlier.locked()["generator"]
PROMPT = (
    SOURCE_PROMPT
    .replace("shared practical purpose that each delegation explicitly gives for continued reporting",
             "shared specific concern that both delegations explicitly express")
    .replace("a short infinitive beginning with 'to'", "a short prepositional phrase beginning with 'about'")
    .replace("supplies no delegation's stated purpose, or the purposes do not overlap",
             "supplies no stated concern, or the two concerns do not match")
)
POSITIVE = {"gb-process", "de-process"}


def read(path):
    return json.loads(path.read_text())


def plan():
    inputs = (Path(__file__), HERE / "protocol.md", HERE.parent / "docket.json", HERE.parent / "provenance.json",
              PRIOR / "purpose_study.py", PRIOR / "plan.json", PRIOR / "scores.json", Path(collector.__file__),
              RELEASE / "release.json")
    return {"pins": {str(p.relative_to(RUNS.parent)): collector.sha(p) for p in inputs},
            "checkpoint_index_sha256": collector.sha(collector.MODEL / "model.safetensors.index.json"),
            "prompt": PROMPT,
            "requests": {name: earlier.earlier.request(name, 45, PROMPT, {
                "delivered": [{"owner": OWNERS[key], "id": key, "text": CARDS[key]} for key in ids]
            }) for name, ids in VIEWS.items()}}


def locked():
    result = plan()
    assert result == read(HERE / "plan.json")
    return result


def native_sentence(name, reply):
    ids = VIEWS[name]
    text = reply["text"]
    if len(ids) != 2 or reply["termination"] != "complete" or len(text.split()) > 14:
        return ""
    if not re.fullmatch(r"about [\w]+(?:[ ’'-][\w]+)*", text, flags=re.IGNORECASE):
        return ""
    first, second = (OWNERS[key] for key in ids)
    return f"{first[0].upper() + first[1:]} and {second} both raised concerns {text}."


def collect(generate, directory):
    for name, spec in locked()["requests"].items():
        reply = generate(spec)
        collector.suite.append(directory / "calls.jsonl", {"id": name, "reply": reply})


def run():
    locked()
    assert os.environ.get("CUDA_VISIBLE_DEVICES", "").startswith("GPU-")
    with patch.object(collector, "roster", return_value={"reform-2553-concern-transfer": CASE}), patch.object(
        collector, "HERE", HERE
    ), patch.object(collector.suite.e, "HERE", RELEASE), patch.object(collector.suite, "collect", collect):
        collector.run(OUT)


def verify():
    config = locked()
    # The previous append runtime replays these same capped generation calls.
    runtime = earlier.earlier.previous.base
    with patch.object(runtime, "HERE", HERE), patch.object(runtime, "OUT", OUT), patch.object(
        runtime, "locked", return_value=config
    ):
        return runtime.verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        print(json.dumps((plan if mode == "plan" else verify)(), ensure_ascii=False, indent=2))
