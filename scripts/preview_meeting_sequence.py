"""CPU-only, non-training-ready demonstration using a completely hand-read meeting."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.meeting_sequence import NEW_TOKENS, digest, render, tokenize_example, validate


def main():
    source_path = ROOT / "data/raw/source-plan-grounding-20261002-v1/record-9214.txt"
    source = source_path.read_text()
    out = ROOT / "research/scenario-role-20261017"
    if (out / "preview.json").exists():
        raise ValueError("Fresh preview required; preserve existing receipts")
    # Literal, manually audited transitions, including events and the chair/national switch.
    specifications = [
        ("The meeting was called", "NONE", "record_event", "UN verbatim record", "before_vote", None),
        ("The President: In accordance", "IND", "council_president", "Mrs. Kamboj", "before_vote", "The President:"),
        ("Mrs. Thomas-Greenfield (United States of America):", "USA", "national_delegation", "Mrs. Thomas-Greenfield", "before_vote", "Mrs. Thomas-Greenfield (United States of America):"),
        ("The President: I shall put", "IND", "council_president", "Mrs. Kamboj", "before_vote", "The President:"),
        ("A vote was taken", "NONE", "record_event", "UN verbatim record", "vote_event", None),
        ("The President: The draft resolution", "IND", "council_president", "Mrs. Kamboj", "after_vote", "The President:"),
        ("Mr. Mythen (Ireland):", "IRL", "national_delegation", "Mr. Mythen", "after_vote", "Mr. Mythen (Ireland):"),
        ("Dame Barbara Woodward (United Kingdom):", "GBR", "national_delegation", "Dame Barbara Woodward", "after_vote", "Dame Barbara Woodward (United Kingdom):"),
        ("Mr. De Almeida Filho (Brazil):", "BRA", "national_delegation", "De Almeida Filho", "after_vote", "Mr. De Almeida Filho (Brazil):"),
        ("Ms. Heimerback (Norway):", "NOR", "national_delegation", "Heimerback", "after_vote", "Ms. Heimerback (Norway):"),
        ("Ms. Evstigneeva (Russian Federation) (spoke in Russian):", "RUS", "national_delegation", "Evstigneeva", "after_vote", "Ms. Evstigneeva (Russian Federation) (spoke in Russian):"),
        ("Mr. Geng Shuang (China) (spoke in Chinese):", "CHN", "national_delegation", "Geng Shuang", "after_vote", "Mr. Geng Shuang (China) (spoke in Chinese):"),
        ("Ms. Dautllari (Albania):", "ALB", "national_delegation", "Dautllari", "after_vote", "Ms. Dautllari (Albania):"),
        ("Mr. Abushahab (United Arab Emirates):", "ARE", "national_delegation", "Abushahab", "after_vote", "Mr. Abushahab (United Arab Emirates):"),
        ("The President: I shall now make", "IND", "council_president", "Mrs. Kamboj", "after_vote", "The President:"),
        ("The measures imposed by the Security Council", "IND", "national_delegation", "Mrs. Kamboj", "after_vote", None),
        ("I now resume my functions", "IND", "council_president", "Mrs. Kamboj", "after_vote", None),
        ("The meeting rose", "NONE", "record_event", "UN verbatim record", "after_vote", None),
    ]
    starts = []
    for anchor, *_ in specifications:
        if source.count(anchor) != 1:
            raise ValueError("Ambiguous literal transition: " + anchor)
        starts.append(source.index(anchor))
    turns = []
    for index, (_, country, capacity, representative, phase, label) in enumerate(specifications):
        start = starts[index]
        end = starts[index + 1] if index + 1 < len(starts) else len(source)
        while source[end - 1].isspace():
            end -= 1
        content = start + (len(label) if label else 0)
        while source[content].isspace():
            content += 1
        turns.append({"start": start, "content_start": content, "end": end, "country": country,
                      "capacity": capacity, "representative": representative, "institution": "UNSC", "phase": phase})
    meeting = {"id": "S/PV.9214", "date": "2022-12-09", "source_path": str(source_path.relative_to(ROOT)),
               "source_sha256": digest(source), "scenario": "UN Security Council; New York; 9 December 2022, 10 a.m.\nAgenda: General issues relating to sanctions.\nDocument before the Council at opening: draft S/2022/925.\nOpening phase: before voting. Later phase changes are supplied only through preceding record events.",
               "turns": turns}
    validate(meeting, source)
    from transformers import AutoTokenizer
    from peft import LoraConfig
    model_path = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    atomic = copy.deepcopy(tokenizer)
    added = atomic.add_special_tokens({"extra_special_tokens": list(NEW_TOKENS)}, replace_extra_special_tokens=False)
    if not set(tokenizer.all_special_ids) <= set(atomic.all_special_ids):
        raise ValueError("Existing special-token flags lost")
    if any(len(atomic.encode(t, add_special_tokens=False)) != 1 for t in NEW_TOKENS):
        raise ValueError("New control token is not atomic")
    config = json.loads((model_path / "config.json").read_text())
    rows = config["text_config"]["vocab_size"]
    examples = []
    for index, turn in enumerate(turns):
        if turn["country"] not in {"GBR", "BRA", "IND"} or turn["capacity"] != "national_delegation":
            continue
        rendered = render(meeting, source, index)
        plain = tokenize_example(tokenizer, rendered)
        tagged = tokenize_example(atomic, rendered)
        if plain["input_ids"][plain["prefix_tokens"]:] != tagged["input_ids"][tagged["prefix_tokens"]:]:
            raise ValueError("Target speech tokens differ across representations")
        examples.append({"country": turn["country"], "target_index": index, "phase": turn["phase"],
                         "history_turns": index, "target_span": rendered["target_source_span"],
                         "prefix_sha256": digest(rendered["prefix"]), "target_sha256": digest(rendered["body"]),
                         "plain": {k: len(v) if isinstance(v, list) else v for k, v in plain.items()},
                         "atomic": {k: len(v) if isinstance(v, list) else v for k, v in tagged.items()}})
        if turn["country"] == "GBR":
            (out / "example-GBR.txt").write_text(rendered["prefix"] + "\n[SUPERVISED COMPLETION STARTS BELOW]\n" + rendered["completion"])
    errors = []
    for messages in ([{"role": "scenario", "content": "Meeting."}], [{"role": "user", "content": "Meeting."}, {"role": "France", "content": "Speech."}]):
        try:
            tokenizer.apply_chat_template(messages, tokenize=False, enable_thinking=False)
        except Exception as exc:
            errors.append({"roles": [m["role"] for m in messages], "error": str(exc)})
    result = {"status": "cpu_representation_preview_not_training_ready", "model_calls": 0, "optimizer_updates": 0,
              "meeting": meeting, "examples": examples, "original_tokenizer_length": len(tokenizer),
              "atomic_tokenizer_length": len(atomic), "model_embedding_rows": rows, "new_tokens_added": added,
              "new_token_ids": {v: atomic.convert_tokens_to_ids(v) for v in NEW_TOKENS},
              "embedding_resize_required": len(atomic) > rows, "tied_embeddings": config["tie_word_embeddings"],
              "peft_trainable_token_indices_available": "trainable_token_indices" in LoraConfig.__dataclass_fields__,
              "custom_role_template_errors": errors,
              "hand_read": f"Same root assistant read complete {len(source)}-character / {len(source.encode())}-byte extracted record, metadata and all selected target/history text; no independent review.",
              "limitations": ["One historically exposed meeting; no fitting or held-event model result.",
                              "Raw extraction retains soft-hyphen/line-wrap artifacts; audited normalization required before fitting.",
                              "France attended but has no recorded national speech here; no French target invented.",
                              "Actual Qwen embedding-row gradients, tied output effects and adapter reload not tested."]}
    (out / "preview.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "examples", "original_tokenizer_length", "atomic_tokenizer_length", "model_embedding_rows", "embedding_resize_required", "custom_role_template_errors")}, indent=2))


if __name__ == "__main__":
    main()
