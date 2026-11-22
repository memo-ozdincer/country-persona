"""Run whole-message evidence selection under reversed local menu order."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import live_2475 as old

CASE, READ, base, prior, frozen = old.CASE, old.READ, old.base, old.prior, old.frozen
wire = prior.wire
OUT = HERE / "evidence"
FULL = READ(PARENT / "oracle.json")["authored_records"]["7"]["answer"].split("\n\n")
PUBLIC = FULL[0]

# Each key is local to its desk. Every selected passage is rendered in this source order.
MENUS = (
    {"1": ("fr-treaty", FULL[1]),
     "2": ("fr-participation", "France linked participation by persons with disabilities to better safety in conflict, humanitarian response and recovery.")},
    {"1": ("ru-article", "Russia read operative paragraph 11 of the resolution as reaching only Article 11 of the convention."),
     "2": ("ru-authority", "Russia opposed new international legal categories for civilian protection."),
     "3": ("ru-article", "Russia supported the resolution's humanitarian aims for persons with disabilities.")},
    {"1": ("uk-participation", "The UK backed disability leadership and disability-disaggregated evidence for Council decisions."),
     "2": ("uk-authority", "The UK agreed with Russia on avoiding new legal obligations."),
     "3": ("uk-authority", "The UK thanked Russia and China for voting in favour despite their doubts.")},
)
# Two related passages share a source block but have distinct source claims.
REQUIRED = {"fr-treaty": (0, "1"), "ru-article": (1, "1"), "ru-authority": (1, "2"),
            "uk-participation": (2, "1"), "uk-authority": (2, "2")}
BRIDGE = FULL[4]
FORMS = wire.forms


def menu(request):
    return list(json.loads(request["messages"][1]["content"])["passages"])


def legal_forms(items):
    return [entry for entry in FORMS(items) if len(entry["ids"]) == len(items) - 1]


def requests():
    for order, desk in product(("normal", "reversed"), range(3)):
        items = list(MENUS[desk].items())
        if order == "reversed":
            items.reverse()
        data = {"task": frozen.public_task(CASE), "desk": CASE["roles"][desk],
                "capacity": len(items) - 1, "passages": {idx: text for idx, (_, text) in items}}
        yield old.old.request(f"{order}/{desk}",
            "Select exactly the requested number of passages from your desk for the Council record. "
            "Prioritize an explicit institutional limit, distinctive reason, or concrete implementation "
            "position over a generic statement of support or thanks. Preserve the object of each legal "
            "qualification and an actionable rationale. Return only a JSON array of passage IDs.", data, 48)


def plan():
    inputs = (Path(__file__), HERE / "protocol.md", PARENT / "docket.json", PARENT / "oracle.json",
              Path(wire.__file__), Path(base.__file__), prior.RELEASE / "release.json")
    rows = list(requests())
    counts = [sum(len(item["forms"]) for item in legal_forms(menu(req))) for req in rows]
    assert len(rows) == 6 and sum(counts) <= 600
    return {"requests": rows, "candidate_counts": counts,
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in inputs}}


def collect(generate, directory):
    wire.STATE["used"] = 0
    for req in plan()["requests"]:
        wire.STATE["request"] = req
        start = perf_counter()
        reply = generate(req)
        assert reply["termination"] == "complete"
        prior.append(directory / "calls.jsonl", {"request": req, "response": reply,
                                                 "elapsed_seconds": perf_counter() - start})
        prior.append(directory / "likelihood.jsonl", wire.STATE.pop("last"))


def run():
    assert plan() == READ(HERE / "plan.json")
    original = base.run

    def launch(directory):
        with patch.object(base, "roster", return_value={CASE["id"]: CASE}):
            original(directory)

    with patch.object(wire, "OUT", OUT), patch.object(wire, "collect", collect), patch.object(
            wire, "forms", legal_forms), patch.object(wire.s, "menu", menu), patch.object(
            base, "run", launch), patch.object(base.suite.e, "HERE", prior.RELEASE), patch.object(base, "HERE", HERE):
        wire.run()


def verify():
    from transformers import AutoTokenizer

    frozen_plan = plan()
    assert frozen_plan == READ(HERE / "plan.json")
    manifest = READ(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl", "likelihood.jsonl"}
    assert all(prior.digest(OUT / name) == value for name, value in manifest.items())
    launch = READ(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["protocol_sha256"] == prior.digest(HERE / "protocol.md")
    assert launch["checkpoint_index_sha256"] == prior.digest(base.MODEL / "model.safetensors.index.json")
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    logs = [prior.wire.n.lines(OUT / k) for k in ("calls.jsonl", "likelihood.jsonl", "tokens.jsonl")]
    selections = {}
    for req, count, call, likelihood, tokens in zip(
            frozen_plan["requests"], frozen_plan["candidate_counts"], *logs, strict=True):
        assert req == call["request"] == likelihood["request"]
        assert base.prompt(tok, req) == tokens["input_ids"]
        got = likelihood["candidates"]
        assert [{**option, "forms": [r["text"] for r in option["forms"]]} for option in got] == legal_forms(menu(req))
        strings = [row for option in got for row in option["forms"]]
        assert len(strings) == count
        for row in strings:
            assert tok.encode(row["text"], add_special_tokens=False) + [eos] == row["tokens"]
        result = wire.summarize(got)
        assert result == likelihood["selection"] and result["selected"] == call["response"]["text"]
        assert call["response"] == tokens["response"]
        assert tok.encode(result["selected"], add_special_tokens=False) + [eos] == tokens["output_ids"]
        selections[req["id"]] = {"native": json.loads(result["selected"]),
                                 "canonical": json.loads(result["canonical_only"]),
                                 "first": menu(req)[:len(menu(req)) - 1],
                                 "input_tokens": call["response"]["input_tokens"],
                                 "output_tokens": call["response"]["output_tokens"],
                                 "elapsed_seconds": call["elapsed_seconds"]}
    return {"selections": selections, "candidate_count": sum(frozen_plan["candidate_counts"]),
            "evidence_sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
