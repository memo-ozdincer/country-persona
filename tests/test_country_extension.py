import csv
import json
import importlib.util
from pathlib import Path

from country_persona.bulk import parse_uhri, parse_unga_dm
from country_persona.io import sha256

spec = importlib.util.spec_from_file_location('country_extension', Path(__file__).parents[1] / 'scripts/prepare_country_extension.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_upr_author_and_respondent_remain_different_countries(tmp_path):
    path = tmp_path / 'uhri.json'
    row = {'AnnotationId': 'x', 'Symbol': 'A/HRC/example', 'Text': 'Protect access to food.',
           'DocumentId': 'd', 'PublicationDate': '2022-01-01', 'AnnotationType': 'Recommendations',
           'Countries': ['India'], 'UprPositions': ['Supported/Noted'], 'UprSession': ['41st Session'],
           'UprRecommendingCountry': ['France'], 'UprCycle': '- Cycle 4', 'Body': '- UPR'}
    path.write_text(json.dumps([row]))
    assert list(parse_uhri(path, countries_only=True)) == []  # Legacy focus unchanged.
    recommendation, response = list(parse_uhri(path, countries_only=True, country_map=module.NAMES))
    assert recommendation['country_iso3'] == 'FRA'
    assert response['country_iso3'] == 'IND'
    assert response['text'] == 'Supported/Noted'
    assert response['question'] == recommendation['text']
    assert module.propose(response) == 'test'


def test_uk_seat_alias_and_vote_amendment_are_preserved(tmp_path):
    path = tmp_path / 'votes.csv'
    r = {'current_seat_name': 'United Kingdom of Great Britain and Northern Ireland',
         'member_state': 'United Kingdom', 'original_seat_name': 'United Kingdom',
         'original_vote': 'abstaining', 'amended_vote': 'in favor', 'vote_was_amended': '1',
         'decision_id': 'decision', 'member_state_id': '42', 'meeting_date': '2022-01-01',
         'decision_topic': 'draft resolution', 'decision_mode': 'recorded vote', 'session_id': '76',
         'meeting_record_id': 'A/76/PV.1', 'draft_resolution_id': 'A/76/L.1', 'resolution_id': 'A/RES/76/1'}
    with path.open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(r)); writer.writeheader(); writer.writerow(r)
    assert list(parse_unga_dm(path)) == []
    result, = parse_unga_dm(path, country_map=module.NAMES)
    assert result['country_iso3'] == 'GBR'
    assert result['text'] == 'abstaining' and result['amended_vote'] == 'in favor'
    assert 'proposal_text_missing' in result['quality_flags']


def test_multilingual_passages_do_not_cross_pdf_pages():
    text = ('Uma política específica. ' * 20) + '\f' + ('Une politique précise. ' * 20)
    r = {'id': 'd', 'text': text, 'source_id': 's', 'source_url': 'https://example.org',
         'raw_sha256': 'a' * 64, 'country_iso3': 'BRA', 'related_countries': ['BRA'],
         'represented_entity': 'Brazil', 'language': 'pt', 'event_date': '2024',
         'available_date': None, 'document_type': 'policy', 'group_id': 'g',
         'split_group': 'g', 'proposed_split': 'train', 'pdf_pages': 2}
    rows = list(module.passages(r, cap=350))
    assert {p['pdf_page'] for p in rows} == {1, 2}
    for p in rows:
        assert p['text'] == text[p['start_char']:p['end_char']]
        assert '\f' not in p['text'] and not p['training_admitted']


def test_presidential_transcript_excludes_overview_and_duplicate_mobile_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'OUT', tmp_path / 'prepared')
    path = tmp_path / 'speech.html'
    transcript = 'La France expose ici une position précise avec ses conditions. ' * 12
    path.write_text('<div class="rich-text">Editorial overview, not the speech.</div>' +
                    f'<div class="card__body ck-styled">{transcript}</div>' * 2)
    row = module.parse_document({'raw_file': str(path), 'raw_sha256': sha256(path),
        'format': 'html', 'source_id': 'france_elysee', 'id': 'test-french-transcript',
        'countries': ['FRA'], 'represented_entity': 'France', 'language': 'fr',
        'date': '2025-09-22', 'date_basis': 'statement date', 'kind': 'national_statement',
        'title': 'Presidential transcript', 'attribution': 'national_representative',
        'group_id': 'event:test', 'url': 'https://example.org', 'retrieved_at': '2026-09-14'})
    assert row['text'] == transcript.strip()
    assert 'Editorial' not in row['text']
