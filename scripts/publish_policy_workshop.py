"""Publish additive workshop files to existing HF repositories, preserving visibility."""
import argparse
import json
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
from huggingface_hub.utils import disable_progress_bars
from build_policy_workshop import ROOT, render_showcase, read_rows, file_hash
from validate_policy_workshop import validate

RELEASE=ROOT/'data/prepared/policy-workshop-20260916'
PREFIX='policy-workshop-20260916'
OWNER='memo-ozdincer'
FULL_REPO=OWNER+'/country-persona-research-files'
PUBLIC_REPO=OWNER+'/country-persona-data'
NAV=f'<a href="{PREFIX}/showcase.html">Policy workshop ↗</a>'


def navigation(text):
    if NAV in text:return text
    if '</nav>' not in text:raise ValueError('Missing navigation anchor')
    return text.replace('</nav>',NAV+'</nav>',1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish',action='store_true')
    args=parser.parse_args()
    validation=validate(RELEASE)
    staging=ROOT/'.cache/policy-workshop-publication';staging.mkdir(parents=True,exist_ok=True)
    public=staging/'public';public.mkdir(exist_ok=True)
    report=json.loads((RELEASE/'build-report.json').read_text())
    cases=json.loads((ROOT/'data/curation/policy_workshop_cases.json').read_text())['cases']
    episodes=read_rows(RELEASE/'episodes.jsonl')
    evidence={r['evidence_id']:r for r in read_rows(RELEASE/'evidence.jsonl')}
    redacted={k:dict(v,excerpt='Exact source text is available in the account-only research files.') for k,v in evidence.items()}
    render_showcase(public/'showcase.html',cases,episodes,redacted,report)
    page=(public/'showcase.html').read_text().replace('Evidence excerpts are exact local-source spans.', 'Exact evidence excerpts are retained in the account-only research files.')
    for name in report['formats']:
        page=page.replace(f'href="{name}.jsonl"',f'href="https://huggingface.co/datasets/{FULL_REPO}/resolve/main/{PREFIX}/{name}.jsonl"')
    page=page.replace('<h2>Export formats</h2>','<h2>Export formats</h2><p>Complete training files require the owner’s Hugging Face login.</p>')
    (public/'showcase.html').write_text(page)
    for e in evidence.values():
        if e['excerpt'] in page:raise ValueError('Source body leaked into public showcase')
    for filename in ['policy_workshop_cases.json','policy_workshop_teams.json']:
        (public/filename).write_bytes((ROOT/'data/curation'/filename).read_bytes())
    refs=[{k:v for k,v in e.items() if k not in {'excerpt','text_file','raw_file'}} for e in evidence.values()]
    (public/'source-references.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in refs))
    readme=(f'# Policy workshop post-training candidates\n\n'
        f'10 policy cases, 53 correlated export rows, 3 authored collaborative workflows. France, UK, India and Brazil.\n\n'
        f'[View the showcase](https://{OWNER}-country-persona-explorer.static.hf.space/{PREFIX}/showcase.html) · '
        f'[Full training files (owner login)](https://huggingface.co/datasets/{FULL_REPO}/tree/main/{PREFIX})\n\n'
        'Public files contain authored tasks, annotations, workflows and source references. Full prompts with exact third-party excerpts remain in the existing private research dataset. '
        'The examples are synthetic, source-grounded candidates, not observed agent runs. All remain unadmitted; independent review is pending. '
        'The four connected source components are too few for a credible held-out benchmark.\n')
    (public/'README.md').write_text(readme)
    private_readme=staging/'private-README.md'
    private_readme.write_text(readme+'\n## Files\n\n20 structured audits, 10 revisions, 10 preference pairs and 13 agent-specific completions. '
        'Every export has a row-aligned provenance manifest. `episodes.jsonl` retains workflow dependencies and `evidence.jsonl` retains exact source spans. '
        'Use completion-only SFT targets; keep rejected answers out of SFT loss. All alternate views share split components. '
        'The complete original source collection is also retained in this repository’s existing research archive.\n\n'
        '[Format and reproduction guide](FORMAT_GUIDE.md)\n')
    api=HfApi()
    if api.whoami()['name']!=OWNER:raise ValueError('Unexpected authenticated owner')
    jobs=[('dataset',FULL_REPO,True),('dataset',PUBLIC_REPO,False),
          ('space',OWNER+'/country-persona-research',True),('space',OWNER+'/country-persona-explorer',False)]
    for kind,repo,private in jobs:
        if api.repo_info(repo,repo_type=kind).private!=private:raise ValueError('Unexpected visibility: '+repo)
    result={'validation':validation,'prefix':PREFIX,'repositories':[]}
    for kind,repo,private in jobs:
        info=api.repo_info(repo,repo_type=kind)
        files={}
        if private:
            files.update({f'{PREFIX}/{p.name}':p for p in RELEASE.iterdir() if p.is_file()})
            files[f'{PREFIX}/README.md']=private_readme
            files[f'{PREFIX}/FORMAT_GUIDE.md']=ROOT/'docs/POLICY_WORKSHOP_POSTTRAINING.md'
            if kind=='dataset':
                for name in ['build_policy_workshop.py','validate_policy_workshop.py','preflight_policy_workshop.py']:
                    files[f'{PREFIX}/scripts/{name}']=ROOT/'scripts'/name
                for name in ['policy_workshop_cases.json','policy_workshop_teams.json']:
                    files[f'{PREFIX}/curation/{name}']=ROOT/'data/curation'/name
                files[f'{PREFIX}/tokenizer-preflight.json']=ROOT/'reports/policy-workshop-preflight.json'
        else:
            files.update({f'{PREFIX}/{p.name}':p for p in public.iterdir() if p.is_file()})
        if kind=='space':
            remote=Path(hf_hub_download(repo,'index.html',repo_type=kind,revision=info.sha))
            staged=staging/(repo.split('/')[-1]+'-index.html')
            staged.write_text(navigation(remote.read_text()))
            files['index.html']=staged
        if not args.publish:
            print(repo,'private:',private,'files:',len(files));continue
        commit=api.create_commit(repo,repo_type=kind,parent_commit=info.sha,
            operations=[CommitOperationAdd(path_in_repo=name,path_or_fileobj=str(p)) for name,p in files.items()],
            commit_message='Add four-country policy workshop formats and review showcase')
        checked={}
        for name,path in files.items():
            downloaded=Path(hf_hub_download(repo,name,repo_type=kind,revision=commit.oid,force_download=True))
            if file_hash(downloaded)!=file_hash(path):raise ValueError('Remote bytes differ: '+name)
            checked[name]=file_hash(path)
        result['repositories'].append({'repo':repo,'repo_type':kind,'private':private,'commit':commit.oid,'sha256_verified_files':checked})
        (ROOT/'reports/policy-workshop-publication.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'repo':repo,'commit':commit.oid,'verified_files':len(checked)}),flush=True)
    if args.publish:
        # Keep subsequent local explorer builds from dropping the additive navigation link.
        for path in [ROOT/'explorer/index.html',ROOT/'.cache/explorer-public-static/index.html',ROOT/'.cache/explorer-private-static/index.html']:
            if path.exists():path.write_text(navigation(path.read_text()))


if __name__=='__main__':
    disable_progress_bars()
    main()
