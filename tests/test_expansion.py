from pathlib import Path
import importlib.util
import pytest
from country_persona.expansion import title_date, parse_briefing, normalized, proposed_split
from country_persona.io import sha256

@pytest.mark.parametrize('title,lang,expected',[
 ('2025年12月31日外交部发言人毛宁主持例行记者会','zh','2025-12-31'),
 ('Conférence de presse du 1er août 2025 tenue par Mao Ning','fr','2025-08-01'),
 ('Conferencia de Prensa Habitual Ofrecida el 31 de Diciembre de 2025 por Mao Ning','es','2025-12-31'),
 ('Очередная пресс-конференция 1 сентября 2025 г.','ru','2025-09-01'),
])
def test_event_date_comes_from_language_title(title,lang,expected):
    assert title_date(title,lang)==expected


def test_reporter_spans_and_history_in_spanish_layout(tmp_path):
    title='Conferencia de Prensa Habitual Ofrecida el 31 de Diciembre de 2025 por Mao Ning'
    q='Reuters: ¿Cuál es la posición de China sobre esta cuestión y el proceso de negociación?'
    a='Mao Ning: China apoya el diálogo. Esta es una respuesta documentada en la conferencia.'
    q2='AFP: ¿Puede aclarar los siguientes pasos?'
    a2='Mao Ning: No tengo más información que proporcionar.'
    path=tmp_path/'briefing.html'
    path.write_text(f'<meta name="ArticleTitle" content="{title}"><meta name="PubDate" content="2026-01-01"><div id="article"><p>{q}</p><p>{a}</p><p>{q2}</p><p>{a2}</p></div>')
    rows=parse_briefing(dict(path=str(path),url='https://example.org/briefing',language='es',source_id='mfa_es',sha256=sha256(path),title=title))
    assert len(rows)==3
    assert rows[0]['group_id']=='mfa:conference:2025-12-31'
    assert rows[0]['proposed_split']=='dev'  # translation was published later
    assert rows[0]['split']=='quarantine'
    assert rows[1]['question']==q
    assert rows[1]['text']==a.split(': ',1)[1]
    assert rows[2]['history'][0]['content']==q
    assert normalized(rows[2]['text']) in normalized(rows[0]['text'])
    assert not rows[1]['training_admitted']


def test_biography_is_not_qa(tmp_path):
    path=tmp_path/'bio.html';path.write_text('<meta name="ArticleTitle" content="Mao Ning"><div class="content_text"><p>Biography</p></div>')
    with pytest.raises(ValueError,match='date'):
        parse_briefing(dict(path=str(path),url='https://example.org/bio',language='fr',source_id='mfa_fr',sha256=sha256(path),title='Mao Ning'))


def test_chunk_offsets_preserve_multilingual_source_text():
    spec=importlib.util.spec_from_file_location('prepare_expansion',Path(__file__).parents[1]/'scripts/prepare_expansion.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    text=('第一段中文。'*35)+'\n\n'+('Une deuxième partie. '*30)+'\f'+('Русский текст. '*40)
    r=dict(id='d1',text=text,group_id='g1',source_id='s',source_url='https://example.org',raw_sha256='a'*64,language='zh',
           country_iso3='CHN',represented_entity='China',event_date='2025-01-01',available_date=None,proposed_split='train',quality_flags=[],pdf_pages=2)
    rows=list(mod.chunks(r,cap=400))
    assert len(rows)>1
    for row in rows:
        assert row['text']==text[row['start_char']:row['end_char']]
        assert len(row['text'])<=400
    assert rows[-1]['pdf_end_page']==2
