#!/usr/bin/env python3
"""Collect publisher-linked strategy PDFs, retaining language versions as one work."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin,quote,urlsplit,urlunsplit
from bs4 import BeautifulSoup
from country_persona.acquire import download
from country_persona.io import digest,write_json
ROOT=Path('data/raw/expansion-20260913')
PAGES={
'germany_china_strategy':'https://www.auswaertiges-amt.de/en/aussenpolitik/regionaleschwerpunkte/asien/strategy-on-china/2608618',
'germany_security_strategy':'https://www.nationalesicherheitsstrategie.de/en.html'}

def discover():
    items={}
    for key,url in PAGES.items():
        path=ROOT/'discovery'/(key+'.html')
        download(url,path,source_id=key,max_bytes=15_000_000)
        soup=BeautifulSoup(path.read_bytes(),'html.parser')
        for a in soup.select('a[href]'):
            u=urljoin(url,a['href']);label=a.get_text(' ',strip=True)
            if not u.lower().endswith('.pdf') or any(t in u.lower() for t in ('summary','zusammenfassung','resume','resumen')):continue
            if key=='germany_china_strategy':
                lang={'English version':'en','German version':'de','Chinese version':'zh'}.get(label)
            else:
                code=u.rsplit('-',1)[-1][:-4].lower();lang={'jp':'ja'}.get(code,code)
            if not lang:continue
            parts=urlsplit(u);u=urlunsplit((parts.scheme,parts.netloc,quote(parts.path,safe='/%'),parts.query,parts.fragment))
            items[u]=dict(url=u,title=key.replace('_',' '),language=lang,country='DEU',group_id=key,
                source_id='national_policy_documents',discovery_url=url,document_date='2023-07-13' if 'china' in key else '2023-06-14',
                date_basis='original_strategy_release; individual translation publication dates unverified')
    u='https://english.mee.gov.cn/Resources/publications/Whitep/202101/P020210122374486901993.pdf'
    items[u]=dict(url=u,title="China's International Development Cooperation in the New Era",language='en',country='CHN',
        group_id='china_development_whitepaper_2021',source_id='national_policy_documents',discovery_url=u,
        document_date='2021-01-10',date_basis='white_paper_release; mirror publication later')
    for lang,name in [('en','National-Security-Strategy-Executive-Summary-EN.pdf'),('de','Sicherheitsstrategie-Zusammenfassung-DE.pdf')]:
        u='https://www.nationalesicherheitsstrategie.de/'+name
        items[u]=dict(url=u,title='Germany National Security Strategy executive summary',language=lang,country='DEU',
          group_id='germany_security_strategy',source_id='national_policy_documents',discovery_url=PAGES['germany_security_strategy'],
          document_date='2023-06-14',date_basis='strategy_release; summary_publication_date_unverified',variant='summary',
          filename='germany_security_strategy-summary-'+lang+'.pdf')
    extras=[
      ('china_ndc_2035','CHN','zh','2025-11-03','China 2035 nationally determined contribution','https://unfccc.int/sites/default/files/2025-11/2035%E5%B9%B4%E4%B8%AD%E5%9B%BD%E5%9B%BD%E5%AE%B6%E8%87%AA%E4%B8%BB%E8%B4%A1%E7%8C%AE%E6%8A%A5%E5%91%8A.pdf','UNFCCC','China'),
      ('eu_ndc_2035',None,'en','2025-11-05','NDC of the European Union and its Member States','https://unfccc.int/sites/default/files/2025-11/DK-2025-11-05%20EU%20NDC.pdf','UNFCCC','European Union and its Member States'),
      ('china_wto_government_report_2024','CHN','en','2024-06-12','WTO Trade Policy Review: report by China WT/TPR/G/458','https://www.wto.org/english/tratop_e/tpr_e/g458_e.pdf','WTO','China'),
    ]
    for key,country,lang,when,title,u,institution,entity in extras:
        items[u]=dict(url=u,title=title,language=lang,country=country,group_id=key,source_id='national_policy_documents',
          discovery_url='https://unfccc.int/NDCREG' if institution=='UNFCCC' else u,
          document_date=when,date_basis='registry_submission_date' if institution=='UNFCCC' else 'report_issue_date; initial_embargo_release_date_unverified',
          institution=institution,represented_entity=entity)
    return list(items.values())

def get(item):
    p=ROOT/'national_policy_documents'/item.get('filename',item['group_id']+'-'+item['language']+'.pdf')
    try:
        rec=download(item['url'],p,source_id=item['source_id'],max_bytes=35_000_000,timeout=30)
        if not p.read_bytes().startswith(b'%PDF'):raise ValueError('Not a PDF')
        return dict(item,path=str(p),sha256=rec['sha256'])
    except Exception as e:return dict(url=item['url'],error=str(e))

def main():
    with ThreadPoolExecutor(max_workers=2) as ex:results=list(ex.map(get,discover()))
    write_json(ROOT/'national_policy_documents/collection.json',dict(documents=[r for r in results if 'error' not in r],errors=[r for r in results if 'error' in r]))
    print('Policy documents',len([r for r in results if 'error' not in r]),[r for r in results if 'error' in r])
if __name__=='__main__':main()
