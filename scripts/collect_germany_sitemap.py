"""Discover mission statement candidates from the publisher's advertised sitemap."""
import gzip
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
from country_persona.acquire import download
from country_persona.io import write_json

root=Path('data/raw/germany_mission')
xml=ET.fromstring(gzip.decompress((root/'sitemap.xml.gz').read_bytes()))
urls=[x.text for x in xml.iter() if x.tag.endswith('loc') and re.search(r'/un-en/[^/]+$',x.text)]
results=[];errors=[]
for i,url in enumerate(urls):
    name=url.rsplit('/',1)[-1]+'.html'
    path=root/'pages'/name
    try:
        receipt=download(url,path,source_id='germany_mission',max_bytes=5_000_000,timeout=30)
        soup=BeautifulSoup(path.read_bytes(),'html.parser')
        title=soup.select_one('meta[property="og:title"]')
        title=title['content'] if title else soup.title.get_text(' ',strip=True)
        main=soup.select_one('main')
        # Preserve non-speech pages as raw only, not model targets.
        if main and re.search(r'\d{2}\.\d{2}\.\d{4}\s*-\s*Speech',main.get_text(' ',strip=True)):
            results.append({'url':url,'path':str(path),'title':title,'sha256':receipt['sha256']})
    except Exception as exc:errors.append({'url':url,'error':str(exc)})
    if i%25==0:
        print(i+1,'/',len(urls),'speeches',len(results),flush=True)
        write_json(root/'sitemap_collection.json',{'documents':results,'errors':errors,'complete':False})
    time.sleep(.2)
write_json(root/'sitemap_collection.json',{'documents':results,'errors':errors,'complete':True,'discovered':len(urls)})
