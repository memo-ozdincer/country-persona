import copy
from collections import Counter
import json
import pytest

from country_persona.meeting_sequence import digest, render, tokenize_example
from country_persona.scenario_sft import schedule, check_row, role_counterfactual, audit_trace, ids_digest


class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(c) for c in text]

    def apply_chat_template(self, messages, **kwargs):
        return self.encode(messages[0]["content"])


def fixture():
    source = "Earlier. Target speech. Future."
    turn = dict(start=0, content_start=0, end=8, country="IRL", representative="A",
                institution="UNSC", capacity="national_delegation", phase="discussion")
    target = {**turn, "start": 9, "content_start": 9, "end": 23, "country": "IND", "representative": "B"}
    meeting = dict(source_sha256=digest(source[:23]), scenario="Dated agenda.", turns=[turn, target])
    rendered = render(meeting, source[:23], 1)
    row = dict(id="case", source="x", country="IND", scenario=meeting["scenario"],
               provenance=dict(source_sha256=digest(source), window=[0, 23], target=[9, 23], turns=[turn, target]),
               **{k: rendered[k] for k in ("prefix", "body", "completion")},
               **tokenize_example(Tokenizer(), rendered), prefix_sha256=digest(rendered["prefix"]),
               target_sha256=digest(rendered["body"]), native_messages=[{"role": "user", "content": "native"}],
               native_prefix_ids=Tokenizer().encode("native"))
    return row, {"x": source}


def test_exact_balance_and_consecutive_updates():
    rows = [{"id": str(i)} for i in range(4)]
    plan = schedule(rows, 32, 42)
    assert [x["step"] for x in plan] == list(range(1, 129))
    assert Counter(x["id"] for x in plan) == Counter({str(i): 32 for i in range(4)})
    assert plan == schedule(rows, 32, 42)
    assert plan != schedule(rows, 32, 43)


@pytest.mark.parametrize("change", ["labels", "input_ids", "prefix", "body", "country", "window", "native"])
def test_corrupt_source_masks_or_inputs_fail(change):
    row, sources = fixture()
    check_row(row, Tokenizer(), sources)
    if change in {"labels", "input_ids"}:
        row[change][0] = 11
    elif change in {"prefix", "body"}:
        row[change] += "invented"
    elif change == "country":
        row["country"] = "GBR"
    elif change == "window":
        row["provenance"]["window"][1] += 1
    else:
        row["native_prefix_ids"][0] += 1
    with pytest.raises(ValueError):
        check_row(row, Tokenizer(), sources)


def test_role_diagnostic_changes_requested_header_only():
    row, _ = fixture()
    wrong = role_counterfactual(row, Tokenizer(), dict(country="GBR", representative="C"))
    assert wrong["input_ids"] != row["input_ids"]
    assert wrong["input_ids"][wrong["prefix_tokens"]:] == row["input_ids"][row["prefix_tokens"]:]
    assert "Earlier." in wrong["prefix"]
    assert "representative=C" in wrong["prefix"]
    assert "Future." not in row["prefix"]


def test_unaccounted_chronological_gap_fails():
    row, sources = fixture()
    row["provenance"]["turns"][0]["end"] = 3
    with pytest.raises(ValueError, match="gap"):
        check_row(row, Tokenizer(), sources)


def test_trace_replay_rejects_tampered_input_mask_or_order(tmp_path):
    row, _ = fixture()
    event = {**schedule([row], 1, 42)[0], "loss": 1.0, "input_ids_sha256": ids_digest(row["input_ids"]),
             "labels_sha256": ids_digest(row["labels"]), "sequence_tokens": len(row["input_ids"]),
             "supervised_tokens": row["supervised_tokens"], "gradient_l2_before_clipping": 0.2,
             "gradient": {"finite": True, "gradient_l2_after_clipping": 0.2}}
    path = tmp_path / "trace.jsonl"
    path.write_text(json.dumps(event) + "\n")
    assert audit_trace(path, [row], 1, 42)["entries"] == 1
    for key, value in [("labels_sha256", "wrong"), ("step", 2), ("loss", float("nan"))]:
        path.write_text(json.dumps({**event, key: value}) + "\n")
        with pytest.raises(ValueError):
            audit_trace(path, [row], 1, 42)
