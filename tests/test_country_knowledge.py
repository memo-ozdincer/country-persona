"""The boundary checks must not merge two national speakers into one target."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('country_knowledge', Path(__file__).parents[1] / 'scripts/prepare_country_knowledge.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def source(text):
    return {'id': 'meeting', '_text': text, 'text_file': 'meeting.txt',
            'text_sha256': 'a' * 64, 'pages': [{'page': 1, 'start': 0, 'end': len(text)}]}


def test_explanation_ends_before_next_speaker_without_blank_line():
    text = 'Mr. A (Brazil): We support with reservations. Mrs. B (Other): We oppose.'
    span = module.source_span(source(text), 'Mr. A (Brazil)', end_before='Mrs. B (Other)')
    assert text[span['char_start']:span['char_end']].strip() == 'Mr. A (Brazil): We support with reservations.'
    assert span['pdf_pages'] == [1]


def test_ambiguous_or_missing_attribution_fails():
    with pytest.raises(ValueError):
        module.source_span(source('Mr. A says yes. Mr. A says no.'), 'Mr. A')
    with pytest.raises(ValueError):
        module.source_span(source('Mr. B says yes.'), 'Mr. A')


def test_missing_next_speaker_does_not_take_remainder_of_document():
    with pytest.raises(ValueError):
        module.source_span(source('Mr. A: yes. Entire other-country corpus.'), 'Mr. A', end_before='Mr. B')
