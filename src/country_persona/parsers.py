"""Source-specific parsers. Unexpected layouts fail rather than becoming silent empty data."""
from __future__ import annotations
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from .schema import record


def soup_for(path):
    # Prefer UTF-8 before optional detectors guess at typographic punctuation.
    # Invalid UTF-8 still falls back to the document's declared encoding.
    return BeautifulSoup(Path(path).read_bytes(), 'html.parser', from_encoding='utf-8')


def paragraphs(node):
    return [p.get_text(' ',strip=True).replace('\u200b','') for p in node.find_all('p') if p.get_text(strip=True)]


def meta(soup,name):
    node=soup.find('meta',attrs={'name':name}) or soup.find('meta',attrs={'property':name})
    return node.get('content','') if node else ''


def english_date(text):
    for pattern,fmt in [(r'\b\d{1,2} [A-Z][a-z]+ \d{4}\b','%d %B %Y'),
                        (r'\b[A-Z][a-z]+ \d{1,2}, \d{4}\b','%B %d, %Y')]:
        m=re.search(pattern,text)
        if m:
            try:return datetime.strptime(m[0],fmt).date().isoformat()
            except ValueError:pass
    return None


def parse_mfa(item):
    path=Path(item['path']);soup=soup_for(path)
    title=' '.join((meta(soup,'ArticleTitle') or item['title']).split())
    published=meta(soup,'PubDate')[:10]
    when=english_date(title) or published
    body=soup.select_one('.content_text')
    if not body or not when:raise ValueError('MFA layout/date missing')
    m=re.search(r'Spokesperson (.+?)[’\']s Regular Press Conference',title)
    if not m:raise ValueError('Spokesperson not identified')
    speaker=m[1]
    key=path.stem;group=f'mfa:conference:{when}'
    text='\n\n'.join(paragraphs(body))
    doc=record('mfa',key,path,item['url'],'CHN',when,'day','foreign_ministry',
               'spokesperson','press_conference',text,title,group=group,available_date=published or when)
    doc['speaker']=speaker
    doc['publication_date']=published or when
    if published and published!=when:doc['quality_flags'].append('event_publication_dates_differ')
    exchanges=[];current_q=None;answer=[];preamble=[];unparsed=[]
    def flush():
        if current_q is not None:
            if answer:exchanges.append((current_q,'\n\n'.join(answer)))
            else:unparsed.append(current_q)
    nodes=[p for p in body.find_all('p') if p.get_text(strip=True)]
    for position,p in enumerate(nodes):
        line=p.get_text(' ',strip=True).replace('\u200b','')
        if not line:continue
        if re.fullmatch(r'[＊*]{3,}',line) or re.fullmatch(r'The following questions? (?:was|were) raised after (?:the |the regular )?press conference[:：]',line):
            flush();current_q=None;answer=[]
            continue
        answer_start=re.match(re.escape(speaker)+r'\s*[:：]\s*(.*)',line)
        # Questions in current archive are bold speaker/outlet-labelled paragraphs.
        bold=p.find(['strong','b'])
        next_line=nodes[position+1].get_text(' ',strip=True) if position+1<len(nodes) else ''
        question_start=bool(not answer_start and (
            (bold and (':' in line or re.match(re.escape(speaker)+r'\s*[:：]',next_line)) and len(bold.get_text(' ',strip=True)) >= len(line)*.8) or
            (re.match(r'[^:：]{1,80}[:：]',line) and re.match(re.escape(speaker)+r'\s*[:：]',next_line))))
        if question_start:
            flush();current_q=line;answer=[]
        elif answer_start:
            if current_q is None:unparsed.append(line)
            else:answer.append(answer_start[1])
        elif current_q is not None and answer:
            answer.append(line)
        elif current_q is None:
            if not exchanges:preamble.append(line)
        else:
            current_q+='\n'+line
    flush()
    if not exchanges:raise ValueError('No confidently attributed Q&A pairs')
    if unparsed:doc['quality_flags'].append('unparsed_exchange')
    out=[doc];history=[]
    for i,(question,answer) in enumerate(exchanges):
        r=record('mfa',f'{key}:qa:{i}',path,item['url'],'CHN',when,'day','foreign_ministry',
                 'spokesperson','authentic_qa',answer,title,question=question,history=copy.deepcopy(history),
                 group=group,available_date=published or when,flags=doc['quality_flags'])
        r.update(parent_id=doc['id'],speaker=speaker,derivation='parsed_authentic_qa',
                 context='\n\n'.join(preamble))
        out.append(r)
        history.extend([{'role':'user','content':question},{'role':'assistant','content':answer}])
    return out


def parse_mission(item,source):
    path=Path(item['path']);soup=soup_for(path);flags=[]
    if source=='germany_mission':
        title=meta(soup,'og:title') or item['title']
        body=soup.select_one('.c-rte--default')
        main=soup.select_one('main')
        m=re.search(r'(\d{2}\.\d{2}\.\d{4})\s*-\s*Speech',main.get_text(' ',strip=True)) if main else None
        if not m:raise ValueError('Not a dated German mission speech')
        published=datetime.strptime(m[1],'%d.%m.%Y').date().isoformat()
        when=english_date(title) or published
        country='DEU'
    else:
        body=soup.select_one('.view-txt')
        wrapper=soup.select_one('.view-content')
        if not wrapper:raise ValueError('Missing China mission wrapper')
        title_node=wrapper.find(['h1','h2'])
        title=title_node.get_text(' ',strip=True) if title_node else item['title'].split('（')[0]
        m=re.search(r'\b(\d{4}-\d{2}-\d{2})\b',wrapper.get_text(' ',strip=True))
        if not m:raise ValueError('Missing China mission publication date')
        published=m[1]
        listed=re.search(r'（(\d{4}-\d{2}-\d{2})）',item.get('title',''))
        when=listed[1] if listed else (english_date(title) or published)
        country='CHN'
    if not body:raise ValueError('Missing mission speech body')
    text='\n\n'.join(paragraphs(body))
    if len(text)<150:raise ValueError('Suspiciously short mission body')
    if when != published:flags.append('event_publication_dates_differ')
    coalition=bool(re.search(r'\b(?:joint statement|on behalf of (?:the )?(?:group|european union|weog|\d+)|joint media stakeout|joint steering)\b',title+'\n'+text[:1600],re.I))
    entity='coalition_requires_attribution' if coalition else ('Germany' if country=='DEU' else 'China')
    if coalition:flags.append('coalition_attribution_review')
    # A UN mission serves many institutions; infer only explicit institution names.
    if re.search(r'security council',title,re.I):institution='UNSC'
    elif re.search(r'general assembly',title,re.I):institution='UNGA'
    elif re.search(r'ECOSOC',title,re.I):institution='ECOSOC'
    elif re.search(r'UNDP|UNFPA|UNOPS',title):institution='UN_development_boards'
    elif re.search(r'peacebuilding commission',title,re.I):institution='UN_Peacebuilding_Commission'
    else:institution='UN_mission_other';flags.append('institution_review')
    phase='explanation_of_vote' if re.search('explanation of vote',title,re.I) else 'statement'
    r=record(source,path.stem,path,item['url'],country,when,'day',institution,
             'coalition_representative' if coalition else 'national_representative',
             'statement_reconstruction',text,title,group=f'un:day:{when}',available_date=published,
             represented_entity=entity,flags=flags)
    r.update(phase=phase,publication_date=published,
             event_date_basis='title_or_archive' if when!=published else 'publication_date_proxy_or_matching_title')
    if r['event_date_basis']=='publication_date_proxy_or_matching_title':
        r['quality_flags'].append('event_date_requires_confirmation')
    return [r]


def parse_german_press(item):
    path=Path(item['path']);soup=soup_for(path)
    title=meta(soup,'og:title') or soup.title.get_text(' ',strip=True)
    title=title.split('|')[0].strip()
    # URL contains an unambiguous German numeric day, month name and year.
    months={'januar':1,'februar':2,'märz':3,'maerz':3,'april':4,'mai':5,'juni':6,
            'juli':7,'august':8,'september':9,'oktober':10,'november':11,'dezember':12}
    m=re.search(r'vom-(\d{1,2})-([a-z]+)-(?:um-)?(\d{4})',item['url'])
    if not m or m[2] not in months:raise ValueError('German conference date not found in URL')
    when=f'{m[3]}-{months[m[2]]:02d}-{int(m[1]):02d}'
    body=soup.select_one('#rs_reading_area_content .bpa-richtext')
    if not body:raise ValueError('German transcript body missing')
    turns=[];speaker=None;parts=[]
    has_speaker_classes=bool(body.select('.Rednerkopf'))
    for p in body.find_all('p'):
        label=p.get_text(' ',strip=True)
        if not label:continue
        fallback_label=(not has_speaker_classes and len(label)<100 and (
            re.fullmatch(r'(?:Frage|Zusatzfrage|Nachfrage)',label,re.I) or
            re.fullmatch(r'[\w .-]+ \([A-Z][A-Za-z0-9]{1,10}\)',label) or
            re.fullmatch(r'(?:SRS|RS) [\w .-]+',label)))
        if 'Rednerkopf' in p.get('class',[]) or fallback_label:
            if speaker and parts:turns.append((speaker,'\n\n'.join(parts)))
            speaker=label;parts=[]
        elif speaker:parts.append(label)
    if speaker and parts:turns.append((speaker,'\n\n'.join(parts)))
    if not turns:raise ValueError('No speaker-labelled German turns')
    group=f'germany_press:conference:{when}'
    doc=record('germany_press',path.stem,path,item['url'],'DEU',when,'day',
               'federal_government','multiple_spokespeople','press_conference',
               '\n\n'.join(s+': '+t for s,t in turns),title,group=group,language='de',available_date=when)
    out=[doc];history=[]
    for i,(speaker,text) in enumerate(turns):
        if '(AA)' in speaker and i and re.match(r'(Frage|Zusatzfrage|Nachfrage)',turns[i-1][0],re.I):
            r=record('germany_press',f'{path.stem}:qa:{i}',path,item['url'],'DEU',when,'day',
                     'foreign_ministry','spokesperson','authentic_qa',text,title,
                     question=turns[i-1][1],history=copy.deepcopy(history[:-1]),group=group,
                     language='de',available_date=when)
            r.update(speaker=speaker,parent_id=doc['id'],derivation='parsed_authentic_qa')
            out.append(r)
        # Other officials are evidence from speakers, never assistant targets for this role.
        history.append({'role':'user','content':speaker+': '+text})
    return out


def parse_ungdc(item):
    path=Path(item['path']);soup=soup_for(path);main=soup.select_one('main')
    # The author site's detail layout has a label/value definition list.
    labels=main.find_all('th') if main else []
    speech=None
    for label in labels:
        if label.get_text(strip=True)=='Speech':speech=label.find_next_sibling('td')
    if speech is None:raise ValueError('UNGDC Speech definition missing')
    text=speech.get_text('\n',strip=True)
    flags=['year_precision_only','historical_entity_review']
    r=record('ungdc_web',path.stem,path,item['url'],item['country'],item['year'],'year',
             'UNGA_General_Debate','national_representative','domain_text',text,
             f"UN General Debate session {item['session']} ({item['year']})",
             group=f"unga:session:{item['session']}",flags=flags)
    r['session']=item['session']
    if item['country']=='CHN' and int(item['year'])<1971:
        r['represented_entity']='Republic of China (historical UN representation)'
        r['quality_flags'].append('not_PRC_training')
    if item['country']=='DEU' and int(item['year'])<1990:
        r['represented_entity']='Federal Republic of Germany (pre-reunification)'
    return [r]
