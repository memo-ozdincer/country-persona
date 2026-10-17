"""Build six source-bound examples; no model loading, generation or optimization."""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import sha256, write_json, write_jsonl
from country_persona.meeting_sequence import END, digest, render, tokenize_example

MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")


def trim_end(source, end):
    while source[end - 1].isspace():
        end -= 1
    return end


def make_turn(source, label, end_label, country, name, phase):
    if source.count(label) != 1 or source.count(end_label) != 1:
        raise ValueError("Ambiguous audited speech boundary")
    start, end = source.index(label), trim_end(source, source.index(end_label))
    content = start + len(label)
    while source[content].isspace():
        content += 1
    return dict(start=start, content_start=content, end=end, country=country, representative=name,
                institution="UNSC", capacity="national_delegation", phase=phase)


def build(source_dir, tokenizer):
    pins = json.loads((source_dir / "sources.json").read_text())
    texts = {x["id"]: (source_dir / x["source"]).read_text() for x in pins["sources"]}
    for pin in pins["sources"]:
        if digest(texts[pin["id"]]) != pin["source_sha256"] or sha256(ROOT / pin["pdf"]) != pin["pdf_sha256"]:
            raise ValueError("Changed official PDF or extracted source")
    scenes = {
        "9214": "UN Security Council; New York; 9 December 2022, 10 a.m.\nAgenda: General issues relating to sanctions.\nDocument before the Council at opening: draft S/2022/925.\nOpening phase: before voting. Later phase changes are supplied only through preceding record events.",
        "8923": "UN Security Council; New York; 9 December 2021, 10 a.m.\nAgenda: Maintenance of international peace and security — Security in the context of terrorism and climate change.\nOpening document: Letter dated 30 November 2021 from Niger, S/2021/988.\nPhase: open debate; this input supplies no subsequent vote or outcome.",
        "9138": "UN Security Council; New York; 27 September 2022, 3 p.m.\nAgenda: Maintenance of peace and security of Ukraine.\nPhase: discussion following briefings; this input supplies no subsequent vote or outcome."
    }
    old = json.loads((ROOT / "research/scenario-role-20261017/preview.json").read_text())["meeting"]
    original = (ROOT / old["source_path"]).read_text()
    turns = copy.deepcopy(old["turns"])
    for t, previous in zip(turns, old["turns"]):
        anchor = original[previous["start"]:previous["start"] + 32]
        body_anchor = original[previous["content_start"]:previous["content_start"] + 32]
        if texts["9214"].count(anchor) != 1 or texts["9214"].count(body_anchor) != 1:
            raise ValueError("Ambiguous transition after reversible normalization")
        t["start"] = texts["9214"].index(anchor)
        t["content_start"] = texts["9214"].index(body_anchor)
    for i, t in enumerate(turns):
        t["end"] = trim_end(texts["9214"], turns[i + 1]["start"] if i + 1 < len(turns) else len(texts["9214"]))
    groups = [("9214", turns, 7, "train"), ("9214", turns, 15, "train")]
    specs = [
        ("8923", "Mr. Nebenzia (Russian Federation) (spoke in Russian):", "Mr. Tirumurti (India):", "Mr. Zhang Jun (China) (spoke in Chinese):", "RUS", "Mr. Nebenzia", "IND", "Mr. Tirumurti", "open_debate", "train"),
        ("8923", "Mr. Pham (Viet Nam) (spoke in French):", "Dame Barbara Woodward (United Kingdom):", "Mr. Kimani (Kenya):", "VNM", "Mr. Pham", "GBR", "Dame Barbara Woodward", "open_debate", "train"),
        ("9138", "Mr. Mythen (Ireland):", "Mrs. Kamboj (India):", "Mr. Agyeman (Ghana):", "IRL", "Mr. Mythen", "IND", "Mrs. Kamboj", "discussion", "eval"),
        ("9138", "Mr. Agyeman (Ghana):", "Mr. Kariuki (United Kingdom):", "Mr. De Almeida Filho (Brazil):", "GHA", "Mr. Agyeman", "GBR", "Mr. Kariuki", "discussion", "eval")]
    for n, prior, current, after, pc, pn, tc, tn, phase, split in specs:
        s = texts[n]
        groups.append((n, [make_turn(s, prior, current, pc, pn, phase), make_turn(s, current, after, tc, tn, phase)], 1, split))
    result = []
    for n, ts, index, split in groups:
        s = texts[n]
        selected = copy.deepcopy(ts[:index + 1])
        # S/PV.9214 has fully audited earlier turns and fits in full. The two long
        # episodes use a complete immediately preceding turn, never a text snippet.
        start = selected[0]["start"]
        end = selected[-1]["end"]
        window = s[start:end]
        for t in selected:
            for k in ("start", "end", "content_start"):
                t[k] -= start
        omitted = n != "9214"
        scene = scenes[n] + ("\nHistory window: only the immediately preceding complete speech is shown; earlier turns are omitted. Their absence is not evidence that a statement was not made." if omitted else "\nHistory window: all earlier body turns are shown; cover metadata is represented in this scenario.")
        meeting = dict(scenario=scene, source_sha256=digest(window), turns=selected)
        rendered = render(meeting, window, len(selected) - 1)
        tokens = tokenize_example(tokenizer, rendered)
        if tokens["prefix_tokens"] + 2048 > 8192:
            raise ValueError("Insufficient untruncated generation budget")
        # Evidence check for the long-record policy: even unlabelled earlier body
        # text is already too long for the fixed budget. No target-aware retrieval.
        body_start = s.index("The meeting was called")
        earlier_raw_tokens = len(tokenizer.encode(s[body_start:ts[index]["start"]], add_special_tokens=False))
        if omitted and earlier_raw_tokens + 2048 <= 8192:
            raise ValueError("Revisit full-history policy; long-history justification no longer holds")
        target = ts[index]
        case_id = f"{n}-{target['country']}"
        mapping = dict(source=n, source_sha256=digest(s), window=[start, end], turns=selected,
                       target=[start + selected[-1]["content_start"], end],
                       prior_history_omitted=omitted, earlier_unlabelled_tokens=earlier_raw_tokens)
        native_user = ("Continue this dated UN Security Council record with the requested national delegation's speech. "
                       "Speak in that institutional capacity; earlier national claims belong to their speakers. "
                       "Do not invent later events or private thoughts. Return only the speech.\n\n" + rendered["prefix"])
        messages = [{"role": "user", "content": native_user}]
        native_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                    enable_thinking=False, return_dict=False)
        if isinstance(native_ids, dict):
            native_ids = native_ids["input_ids"]
        if len(native_ids) + 2048 > 8192:
            raise ValueError("Native control exceeds the same context budget")
        result.append(dict(id=case_id, split=split, country=target["country"], source=n,
                           scenario=scene, provenance=mapping, prefix=rendered["prefix"],
                           body=rendered["body"], completion=rendered["completion"],
                           prefix_sha256=digest(rendered["prefix"]), target_sha256=digest(rendered["body"]),
                           **tokens, native_messages=messages, native_prefix_ids=native_ids))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    rows = build(args.sources, tokenizer)
    args.output.mkdir(parents=True, exist_ok=False)
    for split in ("train", "eval"):
        write_jsonl(args.output / f"{split}.jsonl", [r for r in rows if r["split"] == split])
    overview = []
    for r in rows:
        overview.append({k: r[k] for k in ("id", "split", "country", "source", "prefix_tokens", "supervised_tokens", "prefix_sha256", "target_sha256")})
        (args.output / f"example-{r['id']}.txt").write_text(r["prefix"] + "\n[END OF MASKED PREFIX / BEGIN SUPERVISED AUTHENTIC SPEECH]\n" + r["completion"])
    write_json(args.output / "overview.json", overview)
    lock_files = [p for p in MODEL.iterdir() if p.is_file() and ("tokenizer" in p.name or "jinja" in p.name or p.name == "config.json")]
    write_json(args.output / "tokenizer-lock.json", dict(model="Qwen/Qwen3.5-4B", revision=MODEL.name,
        model_path=str(MODEL), files_sha256={p.name: sha256(p) for p in lock_files},
        transformers="5.17.0", marker_mode="readable_existing_subwords", eos_token=END,
        eos_token_id=tokenizer.convert_tokens_to_ids(END), max_length=8192, max_new_tokens=2048))
    write_json(args.output / "release.json", dict(status="prepared_pending_hand_review_and_runtime_validation",
        examples=overview, independent_review_complete=False, sources=str(args.sources.resolve().relative_to(ROOT)),
        source_files_sha256={p.name: sha256(p) for p in args.sources.iterdir() if p.is_file()},
        files_sha256={p.name: sha256(p) for p in args.output.iterdir() if p.is_file()},
        production_optimizer_updates=0, production_model_calls=0,
        exposure="All records historically exposed in this project and possibly model pretraining. Ukraine excluded from this fit only; development evaluation, not sealed OOD."))
    print(json.dumps(overview, indent=2))


if __name__ == "__main__":
    main()
