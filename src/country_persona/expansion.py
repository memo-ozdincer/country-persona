"""Conservative multilingual parsing for the September 2026 expansion.

Publisher text is evidence, not a generated target. Only explicit reporter /
spokesperson boundaries produce QA candidates. Unknown layouts fail closed.
"""
import copy
from collections import Counter
from datetime import date, datetime
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
from .io import digest
from .parsers import meta, paragraphs
from .schema import record, validate

MONTHS = {
 'fr': 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split(),
 'es': 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split(),
 'ru': 'января февраля марта апреля мая июня июля августа сентября октября ноября декабря'.split(),
}
SPEAKERS = ('毛宁','林剑','郭嘉昆','汪文斌','赵立坚','华春莹',
 'Mao Ning','Lin Jian','Guo Jiakun','Wang Wenbin','Zhao Lijian','Hua Chunying',
 'Мао Нин','Линь Цзянь','Го Цзякунь','Ван Вэньбинь','Чжао Лицзянь','Хуа Чуньин')
ANSWER = re.compile(r'^('+'|'.join(re.escape(s) for s in SPEAKERS)+r')\s*[:：]\s*(.*)', re.I)


def normalized(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text)).casefold()


def title_date(title, language):
    if language == 'zh':
        m = re.search(r'(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日', title)
        if m: return date(*map(int,m.groups())).isoformat()
    else:
        for n, month in enumerate(MONTHS.get(language, []), 1):
            m = re.search(r'(\d{1,2})(?:er)?\s+(?:de\s+)?'+month+r'\s+(?:de\s+)?(20\d{2})', title, re.I)
            if m: return date(int(m[2]),n,int(m[1])).isoformat()
    raise ValueError('No explicit conference event date in title')


def proposed_split(when):
    if not when: return 'quarantine'
    if when <= '2025-12-31': return 'train'
    if when <= '2026-06-30': return 'dev'
    return 'test'


def finish(r, item):
    r.update(training_admitted=False, admission_status='pending_content_and_rights_review',
             text_sha256=digest(normalized(r['text'])),
             language_basis='publisher_language_section', translation_alignment='not_sentence_aligned',
             publication_date=r['available_date'])
    r['proposed_split'] = proposed_split(max(r['event_date'] or '', r['available_date'] or ''))
    if r['source_id']=='germany_aa': r['rights_status']='rights_reserved'
    r['split'] = 'quarantine'  # Candidate release cannot silently enter existing training workflows.
    if r['language'] not in ('en', 'de'):
        r.update(topics=['unclassified'], topic_method='not_assigned; multilingual topic annotation pending')
    return validate(r)


def parse_briefing(item):
    path = Path(item['path']); soup = BeautifulSoup(path.read_bytes(), 'html.parser')
    title = meta(soup, 'ArticleTitle') or item['title']
    lang = item['language']; when = title_date(title,lang)
    # Require the conference title; archive sidebars also link spokesperson bios.
    patterns = {'zh':'例行记者会','fr':r'conférence de presse','es':r'conferencia de prensa','ru':r'пресс-конференц'}
    if not re.search(patterns[lang],title,re.I): raise ValueError('Not a regular press-conference title')
    body = soup.select_one('#News_Body_Txt_A,.content_text,#article')
    if not body: raise ValueError('Missing conference body')
    lines = paragraphs(body)
    if not lines or len('\n\n'.join(lines))<150: raise ValueError('Conference text too short')
    published = meta(soup,'PubDate')[:10]
    date.fromisoformat(published)
    if when > '2026-09-13' or published > '2026-09-13': raise ValueError('Beyond expansion snapshot')
    source = item['source_id']; key = path.stem
    doc = record(source,key,path,item['url'],'CHN',when,'day','foreign_ministry','spokesperson',
                 'press_conference','\n\n'.join(lines),title,language=lang,group=f'mfa:conference:{when}',
                 available_date=published,raw_hash=item['sha256'],flags=['multilingual_extraction_review'])
    doc.update(event_date_basis='explicit_title',translation_status='publisher_original_language' if lang=='zh' else 'publisher_language_version; translator_method_unspecified',
               translation_group=f'mfa:conference:{when}',translation_group_basis='same_institution_conference_date; conservative event grouping, semantic equivalence not adjudicated')
    if when != published: doc['quality_flags'].append('event_publication_dates_differ')
    pairs=[]; orphan=[]; q=None; ans=[]; preamble=[]
    for i,line in enumerate(lines):
        a=ANSWER.match(line)
        next_answer=i+1<len(lines) and ANSWER.match(lines[i+1])
        question = not a and bool(re.match(r'^[^:：]{1,100}\s*[:：]',line)) and next_answer
        if question:
            if q is not None and ans: pairs.append((q,'\n\n'.join(ans)))
            q=line;ans=[]
        elif a:
            if q is not None: ans.append(a[2])
            else: orphan.append(line)
        elif q is not None and ans:
            # Explicit separators/end-of-conference headings must not become answers.
            if re.fullmatch(r'[＊*\s]+',line):
                pairs.append((q,'\n\n'.join(ans)));q=None;ans=[]
            else: ans.append(line)
        elif q is None and not pairs: preamble.append(line)
    if q is not None and ans: pairs.append((q,'\n\n'.join(ans)))
    if orphan: doc['quality_flags'].append('unparsed_spokesperson_turn')
    if not pairs: doc['quality_flags'].append('no_qa_boundaries_extracted')
    out=[finish(doc,item)];history=[]
    for i,(q,a) in enumerate(pairs):
        r=copy.deepcopy(doc);r.update(id=f'{source}:{key}:qa:{i}',source_record_id=f'{key}:qa:{i}',
             task='authentic_qa',text=a,question=q,history=copy.deepcopy(history),
             context='\n\n'.join(preamble),parent_id=doc['id'],derivation='parsed_authentic_qa')
        if normalized(a) not in normalized(doc['text']) or normalized(q) not in normalized(doc['text']):
            raise ValueError('QA does not match a contiguous normalized source span')
        out.append(finish(r,item));history += [{'role':'user','content':q},{'role':'assistant','content':a}]
    return out


def parse_aa(item):
    path=Path(item['path']);soup=BeautifulSoup(path.read_bytes(),'html.parser')
    main=soup.select_one('main');bodies=soup.select('main .c-rte--default')
    if not main or not bodies: raise ValueError('Missing Foreign Office article body')
    title=meta(soup,'og:title') or (main.find('h1').get_text(' ',strip=True) if main.find('h1') else '')
    m=re.search(r'(\d{2}\.\d{2}\.\d{4})\s*[-–]\s*([^\n]+)',main.get_text('\n',strip=True))
    if not m: raise ValueError('No article publication date and type')
    when=datetime.strptime(m[1],'%d.%m.%Y').date().isoformat()
    if when > '2026-09-13': raise ValueError('Beyond snapshot')
    text='\n\n'.join(p for b in bodies for p in paragraphs(b))
    if len(text)<150: raise ValueError('Article too short')
    coalition=bool(re.search(r'joint (?:statement|declaration)|gemeinsame? (?:erklärung|statement)|déclaration conjointe|on behalf of (?:the )?(?:EU|European Union|group)',title+'\n'+text[:1800],re.I))
    flags=['event_date_requires_confirmation','speaker_attribution_review']
    if coalition: flags.append('coalition_attribution_review')
    r=record('germany_aa',path.stem,path,item['url'],'DEU',when,'day','foreign_ministry',
             'coalition_requires_review' if coalition else 'publisher_attribution_requires_review',
             'policy_evidence',text,title,language=item['language'],group=item['translation_group'],
             available_date=when,raw_hash=item['sha256'],represented_entity='coalition_requires_attribution' if coalition else 'Germany',flags=flags)
    r.update(document_type=m[2].strip(),event_date_basis='article_publication_date_proxy',
             translation_status='publisher_language_version; original_language_unspecified',
             translation_group=item['translation_group'],translation_group_basis='publisher_sitemap_hreflang',
             publisher_alternates=item['alternates'])
    return [finish(r,item)]


def parse_mission_zh(item):
    path=Path(item['path']);soup=BeautifulSoup(path.read_bytes(),'html.parser')
    body=soup.select_one('.view-txt');wrapper=soup.select_one('.view-content')
    if not body or not wrapper: raise ValueError('Missing mission body/wrapper')
    heading=wrapper.find(['h1','h2']);title=heading.get_text(' ',strip=True) if heading else item['title']
    m=re.search(r'\b(20\d{2}-\d{2}-\d{2})\b',wrapper.get_text(' ',strip=True))
    if not m: raise ValueError('No publication date')
    when=m[1];date.fromisoformat(when)
    text='\n\n'.join(paragraphs(body))
    if len(text)<100: raise ValueError('Mission text too short')
    coalition=bool(re.search(r'共同发言|联合声明|代表.*(?:国家|小组|集团).*发言',title+'\n'+text[:600]))
    flags=['event_date_requires_confirmation','speaker_attribution_review','multilingual_extraction_review','cross_language_event_link_review']
    if coalition:flags.append('coalition_attribution_review')
    r=record('china_mission_zh',path.stem,path,item['url'],'CHN',when,'day',
             'UNSC' if '安理会' in title else 'UNGA' if '联大' in title else 'UN_mission_other',
             'coalition_requires_review' if coalition else 'publisher_attribution_requires_review',
             'policy_evidence',text,title,language='zh',group=f'un:day:{when}',available_date=when,
             raw_hash=item['sha256'],represented_entity='coalition_requires_attribution' if coalition else 'China',flags=flags)
    r.update(event_date_basis='publication_date_proxy',translation_status='publisher_chinese_version; original_delivery_language_unverified',
             document_type='mission_statement_or_report; review_pending')
    return [finish(r,item)]
