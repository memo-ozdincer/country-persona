"""Run the complete-message decoder against the frozen Resolution 2422 rubric."""
import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[1]
NUMBERED = (HERE.parent / "evidence-reward/verified-record/historical-routing/reward-fit"
            "/family-replay/opposing-contexts/native-writer/source-bound/numbered")
DECODER = NUMBERED / "somalia2753/live/causal/compounded/structured/whole_message"
sys.path.insert(0, str(DECODER))
import whole_message as wire

RELEASE = STUDY / "benchmark-v1.4"
spec = spec_from_file_location("tribunals_v14_evaluate", RELEASE / "evaluate.py")
frozen = module_from_spec(spec)
spec.loader.exec_module(frozen)
CASE = frozen.cases()["tribunals"]
OUT = HERE / "evidence"

PUBLIC = (
    "On 27 June 2018 the Council adopted Peru’s draft S/2018/628 as Resolution 2422, "
    "14–0–1 with Russia abstaining. Serbia participated without a vote. Under Chapter VII "
    "the Council appointed Serge Brammertz Mechanism Prosecutor from 1 July 2018 until "
    "30 June 2020, concluded its progress review and underlined full state cooperation."
)
CARDS = {
    "Peru": {
        "1": ("per-cooperation", "Peru said combating impunity required states to enforce sentences, execute warrants and answer assistance requests."),
        "2": ("per-unity", "Peru called for Council unity behind the Mechanism."),
    },
    "Russia": {
        "1": ("rus-staffing", "Russia linked its abstention to earlier staffing concerns and criticized administration."),
        "2": ("rus-medical", "Russia questioned Mladić’s care and recalled requesting temporary release to Russia under Russian guarantees if prison doctors could not provide treatment."),
    },
    "Serbia": {
        "1": ("srb-release", "Serbia objected that the Mechanism refused temporary medical release despite Serbian guarantees."),
        "2": ("srb-cooperation", "Serbia said it met its cooperation obligations and would prosecute war crimes regardless of nationality."),
    },
}
EXTRA_SOURCES = {"disposition": ("vote",), "capacity": ("vote", "srb-release"),
                 "action": ("action",), "review": ("action",),
                 "contrast": ("per-unity", "rus-staffing")}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def append(path, row):
    wire.n.base.suite.append(path, row)


def requests():
    blocks = frozen.judge.by_id(frozen.evidence(CASE))
    for owner, menu in CARDS.items():
        payload = {"task": frozen.public_task(CASE), "assigned_desk": owner,
                   "public": frozen.visible_blocks(CASE["public"]),
                   "passages": {key: blocks[source]["text"] for key, (source, _) in menu.items()}}
        yield {"id": "tribunals-2422/" + owner, "max_output_tokens": 32, "messages": [
            {"role": "system", "content": (
                "Select each passage from your assigned desk that adds a distinct, material fact, reason or "
                "qualification to the decision record. Preserve why each position was taken, distinguish "
                "positions from Council action, and include all relevant passages. Return only a JSON array "
                "of passage IDs, in source order. Use only supplied evidence."
            )}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def grade(selection):
    source_text = {"vote": PUBLIC, "action": PUBLIC}
    for owner, picks in selection.items():
        assert set(picks) <= CARDS[owner].keys() and len(set(picks)) == len(picks)
        source_text.update(dict(CARDS[owner][key] for key in CARDS[owner] if key in picks))
    answer = " ".join([PUBLIC, *(text for key, text in source_text.items() if key not in ("vote", "action"))])
    calls = [{}, {}, {"text": answer, "termination": "complete"}]
    packet = frozen.final_packet(CASE, calls)
    blocks = frozen.judge.by_id(packet["evidence"])
    units = []
    for criterion in CASE["rubric"]:
        key = criterion["id"]
        need = EXTRA_SOURCES.get(key, (key,))
        met = all(src in source_text for src in need)
        units.append({"id": key, "status": "met" if met else "unmet",
                      "response": " ".join(source_text[src] for src in need) if met else "",
                      "source": [{"block": src, "quote": blocks[src]["text"]} for src in need] if met else [],
                      "reason": "All required attributed clauses are present." if met else
                                "A required desk clause was absent from the rendered record."})
        # The needed excerpts may be separated by other clauses.
        if met and units[-1]["response"] not in answer:
            spans = [source_text[src] for src in need]
            first = min(answer.index(span) for span in spans)
            end = max(answer.index(span) + len(span) for span in spans)
            units[-1]["response"] = answer[first:end]
    marks = {"id": packet["id"], "units": units,
             "guard": {"status": "clear", "source": [], "response": "",
                       "reason": "The fixed clauses keep speaker positions and Council action distinct."}}
    return {"selection": selection, "packet": packet, "marks": marks,
            "score": frozen.final_score(CASE, calls, marks)}


def bank(selection):
    return {str(mask): grade({owner: picks if mask & (1 << i) else []
                              for i, (owner, picks) in enumerate(selection.items())})
            for mask in range(8)}


def plan():
    planned = list(requests())
    controls = bank({owner: list(menu) for owner, menu in CARDS.items()})
    assert all(row["score"]["release"] for row in controls.values())
    assert controls["7"]["score"]["strict"]
    files = (Path(__file__), HERE / "protocol.md", Path(wire.__file__),
             RELEASE / "evaluate.py", RELEASE / "judge_score.py", RELEASE / "release.json",
             RELEASE / "cases.json")
    return {"requests": planned, "candidate_counts": [
                sum(len(option["forms"]) for option in wire.forms(wire.s.menu(row))) for row in planned],
            "authored_scores": [row["score"]["released_70"] for row in controls.values()],
            "sha256": {str(file.relative_to(STUDY)): digest(file) for file in files}}


def collect(generate, directory):
    saved = wire.n.read(HERE / "plan.json")
    assert plan() == saved
    wire.STATE["used"] = 0
    for request in saved["requests"]:
        wire.STATE["request"] = request
        response = generate(request)
        assert response["termination"] == "complete"
        append(directory / "calls.jsonl", {"request": request, "response": response})
        append(directory / "likelihood.jsonl", wire.STATE.pop("last"))


def run():
    assert plan() == wire.n.read(HERE / "plan.json")
    base = wire.n.base
    original = base.run

    def launch(directory):
        with patch.object(base, "roster", return_value={CASE["id"]: CASE}):
            original(directory)

    with patch.object(wire, "OUT", OUT), patch.object(wire, "collect", collect), patch.object(
            base, "run", launch), patch.object(base.suite.e, "HERE", RELEASE), patch.object(base, "HERE", HERE):
        wire.run()


def verify():
    from transformers import AutoTokenizer

    saved = wire.n.read(HERE / "plan.json")
    assert plan() == saved
    manifest = wire.n.read(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "likelihood.jsonl", "calls.jsonl", "tokens.jsonl"}
    assert all(digest(OUT / name) == val for name, val in manifest.items())
    base = wire.n.base
    launch = wire.n.read(OUT / "launch.json")
    assert launch["release_sha256"] == digest(RELEASE / "release.json")
    assert launch["protocol_sha256"] == digest(HERE / "protocol.md")
    assert launch["optimizer_updates"] == 0 and launch["cases"] == [CASE["id"]]
    assert launch["checkpoint"] == str(base.MODEL)
    assert launch["checkpoint_index_sha256"] == digest(base.MODEL / "model.safetensors.index.json")
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    selections, canonical = {}, {}
    logs = [wire.n.lines(OUT / name) for name in ("calls.jsonl", "likelihood.jsonl", "tokens.jsonl")]
    for owner, request, total, call, likelihood, tokens in zip(
            CARDS, saved["requests"], saved["candidate_counts"], *logs, strict=True):
        assert request == call["request"] == likelihood["request"]
        assert base.prompt(tok, request) == tokens["input_ids"]
        candidates = likelihood["candidates"]
        assert [{**option, "forms": [row["text"] for row in option["forms"]]} for option in candidates] == wire.forms(
            wire.s.menu(request))
        forms = [row for option in candidates for row in option["forms"]]
        assert len(forms) == total
        for row in forms:
            assert tok.encode(row["text"], add_special_tokens=False) + [eos] == row["tokens"]
        result = wire.summarize(candidates)
        assert result == likelihood["selection"]
        assert result["selected"] == call["response"]["text"] and call["response"] == tokens["response"]
        assert tok.encode(result["selected"], add_special_tokens=False) + [eos] == tokens["output_ids"]
        selections[owner] = json.loads(result["selected"])
        canonical[owner] = json.loads(result["canonical_only"])
    return {"model_selections": selections, "canonical_only": canonical, "candidate_count": sum(saved["candidate_counts"]),
            "records": {"authored": bank({owner: list(menu) for owner, menu in CARDS.items()}),
                        "model": bank(selections), "canonical_only": bank(canonical)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
