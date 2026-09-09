"""Use the UNGDC authors' public database for China/Germany historical speeches."""
import json
import time
from pathlib import Path
from urllib.parse import urlencode,urljoin
from bs4 import BeautifulSoup
from country_persona.acquire import download
from country_persona.io import write_json

base='https://www.ungdc.bham.ac.uk'
root=Path('data/raw/ungdc')
columns=json.loads((root/'table_init.json').read_text())['columns']
results=[];errors=[]
for country in ('CHN','DEU'):
    params={'draw':'1','start':'0','length':'500','search[value]':'','search[regex]':'false','order[0][column]':'1','order[0][dir]':'desc'}
    for i,c in enumerate(columns):
        for k in ('name','data','searchable','orderable'):
            params[f'columns[{i}][{k}]']=str(c[k]).lower() if isinstance(c[k],bool) else c[k]
        params[f'columns[{i}][search][value]']=''
        params[f'columns[{i}][search][regex]']='false'
    params['columns[3][search][value]']=country
    url=base+'/sessions/ajax_datatable/sessions_table/?'+urlencode(params)
    table_path=root/(country.lower()+'_table.json')
    download(url,table_path,source_id='ungdc_web')
    table=json.loads(table_path.read_text())
    assert len(table['data'])==table['recordsFiltered'], 'Pagination required'
    for raw in table['data']:
        a=BeautifulSoup(raw['data'],'html.parser').select_one('a[href]')
        url=urljoin(base,a['href'])
        name=url.rstrip('/').rsplit('/',1)[-1]
        path=root/'pages'/(name+'.html')
        try:
            receipt=download(url,path,source_id='ungdc_web',max_bytes=2_000_000)
            results.append({'url':url,'path':str(path),'sha256':receipt['sha256'],'country':country,'year':raw['year'],'session':raw['number']})
        except Exception as exc:errors.append({'url':url,'error':str(exc)})
        time.sleep(.2)
    print(country,len(results),flush=True)
write_json(root/'collection.json',{'documents':results,'errors':errors,'complete':True,'coverage':'Author website snapshot; not latest Dataverse bulk release'})
