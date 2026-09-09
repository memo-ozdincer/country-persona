"""Collect official German transcript links from server-rendered archive pagination."""
import json
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from country_persona.acquire import download
from country_persona.io import write_json
root=Path('data/raw/germany_press')
base='https://www.bundesregierung.de/breg-de/aktuelles/pressekonferenzen'
links={};errors=[]
page=0
while True:
    url=base if page==0 else base+f'?page={page}'
    path=root/('index.html' if page==0 else f'archive_{page}.html')
    download(url,path,source_id='germany_press')
    text=path.read_text();match=re.search(r'BPA.initialSearchResultsJson\s*=\s*',text)
    if not match:raise ValueError('Missing archive state')
    result=json.JSONDecoder().raw_decode(text[match.end():])[0]['result']
    if result['page'] != page+1:raise ValueError('Pagination drift')
    for item in result['items']:
        soup=BeautifulSoup(item['payload'],'html.parser')
        for a in soup.select('a[href]'):
            if 'regierungspressekonferenz-vom-' in a['href']:
                links[a['href']]=a.get_text(' ',strip=True)
    page+=1
    if page>=result['pageCount']:break
    time.sleep(.2)
print('Discovered',len(links),'conferences across',page,'pages',flush=True)
results=[]
for i,(url,title) in enumerate(links.items()):
    path=root/'pages'/(url.rsplit('/',1)[-1]+'.html')
    try:
        r=download(url,path,source_id='germany_press',max_bytes=5_000_000,timeout=45)
        results.append({'url':url,'title':title,'path':str(path),'sha256':r['sha256']})
    except Exception as e:errors.append({'url':url,'error':str(e)})
    if i%20==0:
        print(i+1,'/',len(links),flush=True)
        write_json(root/'collection.json',{'documents':results,'errors':errors,'complete':False})
    time.sleep(.2)
write_json(root/'collection.json',{'documents':results,'errors':errors,'discovered':len(links),'complete':True})
