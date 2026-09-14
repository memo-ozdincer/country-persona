"""Stage explicitly separated public catalog and account-only source-data Space."""
import gzip
import json
import shutil
import sqlite3
import tarfile
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache';OUT=CACHE/'data-publication'
PUBLIC=CACHE/'explorer-public';PRIVATE=CACHE/'explorer-private';GITHUB=CACHE/'github-data-catalog'

def main():
    for p in (PUBLIC,PRIVATE,GITHUB):p.mkdir(exist_ok=True)
    for n in ['app.py','index.html','Dockerfile']:shutil.copyfile(ROOT/'explorer'/n,PUBLIC/n)
    shutil.copyfile(OUT/'stats.json',PUBLIC/'stats.json')
    with (OUT/'catalog.sqlite').open('rb') as src,gzip.open(PUBLIC/'catalog.sqlite.gz','wb',compresslevel=6) as dst:shutil.copyfileobj(src,dst)
    (PUBLIC/'README.md').write_text('---\ntitle: Country Persona Explorer\nemoji: 🌐\ncolorFrom: blue\ncolorTo: green\nsdk: docker\napp_port: 7860\npinned: false\n---\n# Country Persona Explorer\n\nCreated and maintained by **Memo Ozdincer**. Public evidence catalog and decision comparisons.\n\n[Download data](https://huggingface.co/datasets/memo-ozdincer/country-persona-data) · [GitHub](https://github.com/memo-ozdincer/country-persona-data)\n')
    for p in PUBLIC.iterdir():
        if p.is_file():shutil.copyfile(p,PRIVATE/p.name)
    (PRIVATE/'README.md').write_text((PUBLIC/'README.md').read_text().replace('Country Persona Explorer','Country Persona Research').replace('Public evidence catalog and decision comparisons.','Account-only full research data, including original source rows and files.'))
    (PRIVATE/'launch.py').write_text('''import os,tarfile,runpy\nfrom pathlib import Path\nroot=Path('/app/research')\nif not (root/'data').exists():\n    root.mkdir(exist_ok=True)\n    with tarfile.open('/app/research.tar.gz') as t:t.extractall(root,filter='data')\nos.environ['PRIVATE_DATA_ROOT']=str(root)\nrunpy.run_path('/app/app.py',run_name='__main__')\n''')
    (PRIVATE/'Dockerfile').write_text((PUBLIC/'Dockerfile').read_text().replace('"app.py"','"launch.py"'))
    db=sqlite3.connect(OUT/'catalog.sqlite');db.row_factory=sqlite3.Row
    with tarfile.open(PRIVATE/'research.tar.gz','w:gz',compresslevel=5) as tar:
        for row in db.execute('SELECT path,bytes FROM files ORDER BY path'):
            p=ROOT/row['path'];assert p.stat().st_size==row['bytes'],str(p)
            tar.add(p,arcname=row['path'],recursive=False)
    for rel in ['explorer/app.py','explorer/index.html','explorer/data-client.js','explorer/Dockerfile','explorer/README.md',
       'scripts/build_data_catalog.py','scripts/build_decision_cases.py','scripts/stage_data_publication.py','scripts/stage_static_explorer.py','scripts/publish_data_catalog.py','src/country_persona/__init__.py','src/country_persona/io.py',
       'docs/DATA_EXPLORER.md','docs/DECISION_CASE_SCHEMA.md','docs/COUNTRY_EXTENSION_EXAMPLES.md',
       'data/source_registry.json','data/rights_registry.json','data/country_extension_registry.json',
       'data/expansion_source_registry.json','data/manifests/decision-cases-20260914.json','reports/data-catalog.json']:
        dst=GITHUB/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dst)
    guide=GITHUB/'docs/DATA_EXPLORER.md'
    guide.write_text(guide.read_text().replace('Existing [training decisions](DECISION_REGISTER.md) and [four-country source methodology](COUNTRY_EXTENSION_20260914.md) retain their literature links.', 'Additional training decisions and source-method notes remain in the original research workspace.'))
    stats=json.loads((OUT/'stats.json').read_text());base='https://memo-ozdincer-country-persona-explorer.static.hf.space/'
    lines=['# Country Persona Data','', '**Created and maintained by Memo Ozdincer.**', '',
      'Dated evidence, public policy positions and recorded decisions for country-persona research.','',
      '**[Open the interactive explorer](https://huggingface.co/spaces/memo-ozdincer/country-persona-explorer)** · [Download the tables](https://huggingface.co/datasets/memo-ozdincer/country-persona-data) · [Full research view (owner login)](https://huggingface.co/spaces/memo-ozdincer/country-persona-research)','',
      '## Start with substance','',
      f'- [Compare six countries on the same UN decisions]({base}#view=compare)',
      f'- [Read actual policy positions]({base}#kind=policy_positions&view=explore)',
      f'- [Inspect country statistics]({base}#kind=country_statistics&view=explore)',
      '- [Read the 12 policy applications](docs/COUNTRY_EXTENSION_EXAMPLES.md)',
      '- [Understand the decision-case format](docs/DECISION_CASE_SCHEMA.md)','',
      '## Browse by country','', '| Country | Distinct record objects with that attribution | Browse |','|---|---:|---|']
    (GITHUB/'countries').mkdir(exist_ok=True)
    for code,name in stats['countries'].items():
        lines.append(f'| [{name}](countries/{code}.md) | {stats["country_counts"][code]:,} | [Open]({base}#country={code}&view=explore) |')
        rows=[dict(r) for r in db.execute("SELECT r.* FROM records r JOIN record_countries c ON c.uid=r.uid WHERE c.country=? AND r.kind IN ('policy_positions','decision_cases') ORDER BY kind,date DESC",(code,))]
        body=[f'# {name}','',f'[Open all {name} records]({base}#country={code}&view=explore) · [Statistics]({base}#country={code}&kind=country_statistics&view=explore)','', 'Country attribution identifies the speaker or represented institution, not the population’s personality. Joint and EU positions retain institutional scope.','']
        for r in rows:
            body.extend([f'## {r["title"]} · {r["date"] or "Date unknown"}', '',r['summary'],'',f'[Inspect evidence and complete record]({base}#'+urlencode({'id':r['uid'],'view':'explore','country':code,'kind':r['kind']})+')',''])
        (GITHUB/'countries'/f'{code}.md').write_text('\n'.join(body).rstrip()+'\n')
    lines+=['','## Coverage and limitations','',
      f'The catalog indexes **{stats["exact_unique_records"]:,} exact distinct JSON record objects** from **{stats["input_rows"]:,} row occurrences** across **{stats["input_jsonl_files"]} files**, plus an inventory of **{stats["inventory_files"]:,} source and prepared files**. These counts include overlapping translations, review manifests and alternative training views; they are not independent examples.', '',
      '**12 decision cases** cover two UN resolutions and six countries. Seven have an attributed statement; five still lack one. Twenty policy records and fifteen authored applications are available across the prototype and extension. New cases are quarantined retrospective demonstrations, not a hidden benchmark or proof of persona quality.','',
      'Public downloads contain metadata, factual values and project-authored summaries. Original source bodies and original QA remain in the account-only research view where reuse is unresolved or reserved. Publisher links and attribution remain visible for everyone.','',
      '## Documentation','',
      '- [Exploration guide, counts and update workflow](docs/DATA_EXPLORER.md)',
      '- [Attribution and source credits](ATTRIBUTION.md)',
      '- [Source registry](data/source_registry.json)',
      '- [Four-country official-source registry](data/country_extension_registry.json)',
      '- [Source-use status](data/rights_registry.json)',
      '- [Generated coverage report](reports/data-catalog.json)','',
      'The hosted explorer is static and read-only; it requires no paid compute. It does not call a model or launch training. This is a presentation companion to the original research workspace. Rebuilding requires its private source snapshots and preparation library.']
    (GITHUB/'README.md').write_text('\n'.join(lines)+'\n')
    (GITHUB/'ATTRIBUTION.md').write_text('''# Attribution

Project owner, maintainer and publisher: **Memo Ozdincer** (`memo-ozdincer`). Git commits use the owner's configured identity; no agent account is the repository author.

Government statements remain attributable to the named national representative or institution, including foreign ministries, national governments and UN missions. Joint statements and EU documents retain their collective scope. Official records, resolutions, UPR material and parallel documents are credited to the United Nations and OHCHR as applicable. Country statistics retain World Bank indicator identities and upstream provider metadata. UNGA-DM, Speaking Volumes and the General Debate Corpus retain their researcher/provider source records in the registries and row provenance.

Project ownership is not a claim of authorship of third-party sources. Generated summaries and preparation are labeled as assistant-prepared derivations; they are not authentic historical dialogue or independently reviewed expert annotations. No blanket license is imposed on the underlying corpus. Refer to each source's terms and the source-use registry.
''')
    (GITHUB/'CITATION.cff').write_text('''cff-version: 1.2.0
message: "Please cite this research catalog when using its prepared representations. Cite the original sources separately."
title: "Country Persona Data"
authors:
  - family-names: Ozdincer
    given-names: Memo
version: "2026.09.14"
date-released: "2026-09-14"
url: "https://github.com/memo-ozdincer/country-persona-data"
repository-code: "https://github.com/memo-ozdincer/country-persona-data"
''')
    (GITHUB/'requirements.txt').write_text('pyarrow==25.0.1\nhuggingface_hub==0.36.2\n')
    (GITHUB/'.gitignore').write_text('.cache/\n.venv/\n__pycache__/\ndata/raw/\ndata/prepared/\ndata/canonical/\n*.sqlite\n*.sqlite.gz\nresearch.tar.gz\n.env*\n')
    for f in GITHUB.rglob('*.md'):f.write_text(f.read_text().rstrip()+'\n')
    print({'public_space_bytes':sum(p.stat().st_size for p in PUBLIC.iterdir() if p.is_file()),'private_space_bytes':sum(p.stat().st_size for p in PRIVATE.iterdir() if p.is_file()),'github_directory':str(GITHUB)})
if __name__=='__main__':main()
