"""Publishable coverage-only view: no Reddit bodies, account names or record IDs."""
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RELEASE='reddit-country-20260923'


def build():
    out=ROOT/'data/prepared'/RELEASE
    report=json.loads((out/'coverage.json').read_text())
    registry=json.loads((ROOT/'data/reddit_source_registry.json').read_text())
    public=ROOT/'.cache/reddit-publication/public';public.mkdir(parents=True,exist_ok=True)
    # Explicit public allowlist: aggregate statistics and dataset provenance only.
    view={k:report[k] for k in ['release','country_basis','raw_bytes_verified','raw_files_verified','source_repositories','raw_rows_scanned','unique_prepared_records','countries','training_admitted','coverage_note','limitations','cross_thread_exact_duplicate_text_groups','comments_with_missing_direct_parent']}
    (public/'coverage.json').write_text(json.dumps(view,ensure_ascii=False,indent=2)+'\n')
    (public/'source-registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    esc=lambda x:html.escape(str(x))
    fmt=lambda n:f'{n:,}'
    full='https://huggingface.co/datasets/memo-ozdincer/country-persona-research-files/tree/main/'+RELEASE
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reddit datasets by country</title>',
     '<style>body{background:#f3f5f7;color:#1e303c;font:16px/1.65 system-ui,sans-serif;margin:0}main{max-width:1160px;margin:auto;padding:32px 24px}h1{font-size:32px}h2{margin-top:36px}a{color:#075d79}section{background:white;padding:24px;border:1px solid #dbe3e8;border-radius:12px;margin:20px 0}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:10px;border-bottom:1px solid #e1e7eb}th{font-size:14px;color:#48616e}small{color:#496271}.scroll{overflow-x:auto}.counts{display:flex;flex-wrap:wrap;gap:12px}.counts span{background:#e6edf2;padding:7px 12px;border-radius:6px}nav{display:flex;gap:18px;flex-wrap:wrap}code{font-size:13px;overflow-wrap:anywhere}li{margin:8px 0}</style></head><body><main>',
     '<nav><a href="../index.html">Country explorer</a><a href="'+full+'">Prepared files · owner login</a><a href="source-registry.json">Source registry</a></nav><h1>Reddit datasets by country</h1>',
     '<p>Country-related communities, with separate post and comment records. These labels describe the community’s subject or locality, not its members’ nationality or national public opinion.</p>',
     '<div class="counts"><span>'+fmt(report['unique_prepared_records'])+' unique records</span><span>'+fmt(sum(c['observed_reply_pairs'] for c in report['countries'].values()))+' observed parent–reply pairs</span><span>'+str(report['source_repositories'])+' source datasets</span><span>'+str(report['raw_files_verified'])+' verified archive files</span></div>',
     '<p>All records remain research candidates. Reply pairs preserve observed links but may omit earlier conversation. No Reddit replies were promoted to factual gold answers or training-approved targets.</p>',
     '<section><div class="scroll"><table><thead><tr><th>Country context</th><th>Posts</th><th>Comments</th><th>Reply pairs</th><th>Communities</th></tr></thead><tbody>']
    for c,d in report['countries'].items():
        parts.append(f'<tr><td><a href="#{c}">{esc(d["name"])}</a></td><td>{fmt(d["record_types"].get("post",0))}</td><td>{fmt(d["record_types"].get("comment",0))}</td><td>{fmt(d["observed_reply_pairs"])}</td><td>{len(d["subreddits"])}</td></tr>')
    parts+=['</tbody></table></div></section><h2>Coverage</h2><p>'+esc(report['coverage_note'])+'</p><p>Earliest and latest dates below are endpoints across discontinuous source collections, not a claim of complete intervening coverage.</p>']
    for c,d in report['countries'].items():
        start,end=(d['date_bounds'] or ['unknown','unknown'])
        parts += [f'<section id="{c}"><h2>{esc(d["name"])}</h2><p>{fmt(d["records"])} records · {fmt(d["observed_reply_pairs"])} linked replies · {esc(start[:10])} to {esc(end[:10])}</p>',
                  '<div class="scroll"><table><thead><tr><th>Community</th><th>Records</th></tr></thead><tbody>']
        for sub,n in sorted(d['subreddits'].items(),key=lambda x:(-x[1],x[0])):
            parts.append(f'<tr><td>r/{esc(sub)}</td><td>{fmt(n)}</td></tr>')
        parts+=['</tbody></table></div>',f'<p><a href="{full}/{c}">Download {esc(d["name"])} files</a></p>']
        if d['planned_but_unobserved_subreddits']:parts+=['<small>Not observed in the selected files: '+esc(', '.join('r/'+s for s in d['planned_but_unobserved_subreddits']))+'. This does not establish that those communities were empty.</small>']
        parts+=['</section>']
    parts+=['<h2>Acquired datasets</h2>']
    for s in registry['sources']:
        parts+=['<section><h3><a href="'+esc(s['url'])+'">'+esc(s['repository'])+'</a></h3><p>'+str(len(s['files']))+' files · '+f'{sum(f["bytes"] for f in s["files"])/1e9:.2f}'+' GB · pinned revision <code>'+esc(s['revision'])+'</code></p></section>']
    parts+=['<h2>Other datasets inspected</h2><div class="scroll"><table><thead><tr><th>Dataset</th><th>Status</th><th>Finding</th></tr></thead><tbody>']
    for s in registry['reviewed_alternatives']:
        parts.append('<tr><td><a href="'+esc(s['url'])+'">'+esc(s['id'])+'</a></td><td>'+esc(s['status'].replace('_',' '))+'</td><td>'+esc(s['reason'])+'</td></tr>')
    parts+=['</tbody></table></div><h2>Quality and use</h2><ul>']+['<li>'+esc(x)+'</li>' for x in report['limitations']]
    parts+=['</ul><p>Publisher labels and repository licenses do not by themselves establish rights in user-authored content. <a href="https://redditinc.com/policies/data-api-terms">Reddit’s API terms</a> and the <a href="https://support.reddithelp.com/hc/en-us/articles/49381918834964-Reddit-for-Researchers-Program">researcher program</a> are recorded in the source registry. Source text is omitted from this public view.</p></main></body></html>']
    (public/'index.html').write_text('\n'.join(parts)+'\n')
    (public/'README.md').write_text('# Reddit country-context collection\n\n'+f'{report["unique_prepared_records"]:,} unique prepared records from four pinned public dataset repositories.\n\n'+f'[Coverage explorer](https://memo-ozdincer-country-persona-explorer.static.hf.space/{RELEASE}/index.html) · [Full prepared files (owner login)]({full})\n\nCountry context belongs to communities, not individual authors. All records are quarantined, not training-approved. Public files contain aggregate counts and source provenance; source bodies remain in the private research collection.\n')
    print('Built coverage-only public view:',public)


if __name__=='__main__':build()
