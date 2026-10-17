import pytest

from country_persona.meeting_sequence import END, NEW_TOKENS, digest, render, tokenize_example, validate


@pytest.fixture
def fixture():
    source = "Context. First speech. Future secret."
    offsets = [(0, 8), (9, 22), (23, len(source))]
    turns = [{"start": a, "end": b, "country": c, "institution": "UNSC", "capacity": role,
              "representative": "Test speaker", "phase": "before_vote"}
             for (a, b), c, role in zip(offsets, ("IND", "GBR", "BRA"),
                                        ("council_president", "national_delegation", "national_delegation"))]
    return {"source_sha256": digest(source), "scenario": "An agenda supplied before the speeches.", "turns": turns}, source


def test_chronology_excludes_target_and_future_from_context(fixture):
    meeting, source = fixture
    row = render(meeting, source, 1)
    assert "Context." in row["prefix"]
    assert "First speech." not in row["prefix"]
    assert "Future secret." not in row["prefix"]
    assert row["completion"] == "First speech." + END


def test_chair_and_national_capacity_remain_separate(fixture):
    meeting, source = fixture
    text = render(meeting, source, 1)["prefix"]
    assert "country=<|country_IND|>; institution=UNSC; capacity=council_president" in text
    assert "country=<|country_GBR|>; institution=UNSC; capacity=national_delegation" in text


def test_changed_source_and_undeclared_gaps_rejected(fixture):
    meeting, source = fixture
    with pytest.raises(ValueError, match="Source bytes"):
        validate(meeting, source + "mutation")
    meeting["turns"][1]["start"] += 2
    with pytest.raises(ValueError, match="gap"):
        validate(meeting, source)


def test_marker_injection_rejected(fixture):
    meeting, source = fixture
    meeting["scenario"] += NEW_TOKENS[0]
    with pytest.raises(ValueError, match="Reserved marker"):
        validate(meeting, source)


def test_speaker_label_is_context_metadata_not_supervised_body(fixture):
    meeting, source = fixture
    meeting["turns"][1]["content_start"] = 15
    row = render(meeting, source, 1)
    assert row["body"] == "speech."


def test_loss_mask_and_truncation_guard(fixture):
    class CharacterTokenizer:
        def encode(self, text, add_special_tokens=False):
            return [ord(c) for c in text]
    meeting, source = fixture
    row = render(meeting, source, 1)
    encoded = tokenize_example(CharacterTokenizer(), row)
    n = encoded["prefix_tokens"]
    assert all(v == -100 for v in encoded["labels"][:n])
    assert encoded["labels"][n:] == encoded["input_ids"][n:]
    with pytest.raises(ValueError, match="no silent truncation"):
        tokenize_example(CharacterTokenizer(), row, max_length=5)


def test_unstable_token_boundary_is_rejected(fixture):
    class BadTokenizer:
        def encode(self, text, add_special_tokens=False):
            return [len(text)]
    meeting, source = fixture
    with pytest.raises(ValueError, match="prefix-stable"):
        tokenize_example(BadTokenizer(), render(meeting, source, 1))
