"""Recover and publish the exact original pilot; no model work or payload rewriting."""
import collections,csv,hashlib,io,json,os,re,subprocess,sys,tarfile,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
ROOT=Path(__file__).resolve().parent
OLD='memo-ozdincer/country-persona-research-files'
REV='bd8e2c90e72982ada3bdf2fad8137af9fa27a604'
NEW='memo-ozdincer/country-persona-aurora-data'
PARENT='1db3b0864858f2ba47010f608b14e7206d93a751'
TAG='aurora-20261029-v4'
token=Path(os.environ['HF_TOKEN_PATH']).read_text().strip()
api=HfApi(token=token)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(name,d):
 p=ROOT/name
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def anon(path):
 with urllib.request.urlopen('https://huggingface.co/datasets/'+NEW+'/resolve/'+TAG+'/'+path,timeout=60) as r:
  assert r.status==200
  return r.read()
inventory=json.loads(Path(hf_hub_download(OLD,'file-inventory.json',repo_type='dataset',revision=REV,token=token)).read_text())
selected={r['path']:r for r in inventory if r['path'].startswith('data/prepared/pilot/')}
assert len(selected)==53
print('Downloading original archive to scratch cache',flush=True)
archive=Path(hf_hub_download(OLD,'research.tar.gz',repo_type='dataset',revision=REV,token=token))
assert digest(archive)=='e8f039156487ccdb270dad883c3989f0bc253125f53e3b00e7a8839e26489025'
found=set()
with tarfile.open(archive,'r|gz') as tar:
 for member in tar:
  name=member.name.removeprefix('./')
  if name not in selected:continue
  assert member.isfile() and name not in found
  raw=tar.extractfile(member).read(); record=selected[name]
  assert len(raw)==record['bytes'] and sha(raw)==record['sha256'],name
  assert token.encode() not in raw
  for pattern in [rb'hf_[A-Za-z0-9]{20,}',rb'gh[pousr]_[A-Za-z0-9]{20,}',rb'github_pat_[A-Za-z0-9_]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']:
   assert not re.search(pattern,raw),name
  p=ROOT/'workspace'/name;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert p.read_bytes()==raw
  else:
   with p.open('xb') as f:f.write(raw)
  found.add(name)
assert found==set(selected)
print('53 original files recovered and SHA-256 verified',flush=True)
pilot=ROOT/'workspace/data/prepared/pilot'
counts={}; all_ids=set(); canonical_ids=set()
with (pilot/'pilot.canonical.jsonl').open() as f:
 for line in f:
  if not line.strip():continue
  row=json.loads(line);assert row['id'] not in canonical_ids;canonical_ids.add(row['id'])
assert len(canonical_ids)==37094
for p in sorted((pilot/'candidates').rglob('*.sft.jsonl')):
 manifest=p.with_name(p.name.replace('.sft.jsonl','.manifest.jsonl'))
 rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
 meta=[json.loads(x) for x in manifest.read_text().splitlines() if x.strip()]
 assert len(rows)==len(meta)
 for index,(row,metadata) in enumerate(zip(rows,meta,strict=True)):
  assert isinstance(row['prompt'],list) and isinstance(row['completion'],list)
  assert row['completion'][-1]['role']=='assistant'
  assert all(isinstance(m['content'],str) and m['content'] for m in row['prompt']+row['completion'])
  assert metadata['row_index']==index and metadata['id'] in canonical_ids
 counts[str(p.relative_to(pilot))]=len(rows)
assert sum(counts.values())==16373
build=json.loads((pilot/'build_report.json').read_text())
assert build['pilot_records']==37094
for name,n in counts.items():
 bits=Path(name).parts
 key='/'.join([bits[1],bits[2],bits[3].split('.')[0]])
 assert build['candidates'][key]==n
report={'status':'original_pilot_recovered_and_counts_verified','source_repo':OLD,'source_revision':REV,
 'archive_sha256':digest(archive),'files':53,'bytes':sum(r['bytes'] for r in selected.values()),
 'canonical_records':37094,'sft_candidates':16373,'sft_counts':counts,
 'candidate_and_country_directories_are_same_collection':True,'source_sha256_all_match':True,
 'credential_scan_passed':True,'new_model_calls':0,'new_optimizer_updates':0,'research_goal_status':'paused'}
save('preparation.json',report)
entries=[]
for name,r in sorted(selected.items()):
 raw=(ROOT/'workspace'/name).read_bytes()
 entries.append({'path':'workspace/'+name,'bytes':len(raw),'sha256':sha(raw),
 'git_blob_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()})
supplement=dict(report,files=entries,original_aurora_manifest_unchanged=True)
save('PILOT_MANIFEST.json',supplement)
manifest_sha=digest(ROOT/'PILOT_MANIFEST.json')
verifier='''"""Verify the original China/Germany pilot with Python standard library."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--prefix',default='');a=p.parse_args()
raw=(a.root/'PILOT_MANIFEST.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()==EXPECTED_MANIFEST_SHA256,'Manifest mismatch'
entries=[e for e in json.loads(raw)['files'] if e['path'].startswith(a.prefix)]
assert entries,'No selected files'
for e in entries:
 rel=Path(e['path']);assert not rel.is_absolute() and '..' not in rel.parts
 f=a.root/rel;assert not f.is_symlink() and f.is_file() and f.stat().st_size==e['bytes'],e['path']
 assert hashlib.sha256(f.read_bytes()).hexdigest()==e['sha256'],e['path']
print(json.dumps({'status':'verified','files':len(entries),'bytes':sum(e['bytes'] for e in entries)}))
'''
verifier=verifier.replace('import argparse,hashlib,json', 'EXPECTED_MANIFEST_SHA256='+repr(manifest_sha)+'\nimport argparse,hashlib,json')
(ROOT/'VERIFY_PILOT_DOWNLOAD.py').write_text(verifier)
subprocess.run([sys.executable,'-B',str(ROOT/'VERIFY_PILOT_DOWNLOAD.py')],check=True)
info=api.repo_info(NEW,repo_type='dataset');assert info.sha==PARENT and not info.private
card=Path(hf_hub_download(NEW,'README.md',repo_type='dataset',revision=PARENT,token=False)).read_text()
section='''## China/Germany original pilot — added 29 October

The full original pilot is now included: **37,094 canonical records and 16,373 SFT-format candidates**, in 53 original files (335,534,335 bytes). The 16,373 candidates are the China/Germany folders below, not an additional independent collection. All original bytes match the September archive inventory. These are historical candidates with original review/use statuses, not newly admitted training examples or new model results.

- [China: full prompts, answers and manifests](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261029-v4/workspace/data/prepared/pilot/candidates/CHN)
- [Germany: full prompts, answers and manifests](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261029-v4/workspace/data/prepared/pilot/candidates/DEU)
- [37,094-record canonical pool](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/resolve/aurora-20261029-v4/workspace/data/prepared/pilot/pilot.canonical.jsonl?download=true)
- [Splits, admission ledger and build report](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data/tree/aurora-20261029-v4/workspace/data/prepared/pilot)

Download with `revision="aurora-20261029-v4"`, `token=False`, and optional `allow_patterns=["workspace/data/prepared/pilot/**", "PILOT_MANIFEST.json", "VERIFY_PILOT_DOWNLOAD.py"]`. Then run `python3 -B country-persona-aurora-data/VERIFY_PILOT_DOWNLOAD.py`.

The original `FILE_MANIFEST.json`/`VERIFY_DOWNLOAD.py` still cover the unchanged 15,826-file Aurora payload. `PILOT_MANIFEST.json` and `VERIFY_PILOT_DOWNLOAD.py` cover the 53 added pilot files. Combined: **15,879 payload files / 6,778,439,838 bytes**. Older raw/canonical source collections outside this pilot have not been newly exported.

'''
card=card.replace('This public dataset contains **15,826 files / 6,442,905,503 bytes (6.44 GB)**:', 'The original Aurora export contains **15,826 files / 6,442,905,503 bytes (6.44 GB)**:')
card=card.replace('## Start here',section+'## Start here').replace('revision="aurora-20261024-v3"','revision="'+TAG+'"')
(ROOT/'README.md').write_text(card)
status=json.loads(Path(hf_hub_download(NEW,'STATUS.json',repo_type='dataset',revision=PARENT,token=False)).read_text())
status.update({'recommended_tag':TAG,'pilot_supplement':report,'pilot_manifest_sha256':manifest_sha,
 'combined_payload_files':15879,'combined_payload_bytes':6778439838,'metadata_updated_at':datetime.now(timezone.utc).isoformat()})
save('STATUS.json',status)
operations=[CommitOperationAdd(path_in_repo=e['path'],path_or_fileobj=str(ROOT/e['path'])) for e in entries]
operations += [CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(ROOT/n)) for n in ['README.md','STATUS.json','PILOT_MANIFEST.json','VERIFY_PILOT_DOWNLOAD.py']]
print('Uploading 53 verified pilot files',flush=True)
c=api.create_commit(NEW,repo_type='dataset',parent_commit=PARENT,operations=operations,commit_message='Add original China/Germany pilot: 37094 canonical and 16373 SFT candidates')
save('upload-commit.json',{'commit':c.oid,'tag':TAG})
remote=api.get_paths_info(NEW,paths=[e['path'] for e in entries],repo_type='dataset',revision=c.oid)
remote={r.path:r for r in remote}
for e in entries:
 r=remote[e['path']];assert r.size==e['bytes']
 assert (r.lfs.sha256==e['sha256']) if r.lfs else (r.blob_id==e['git_blob_sha1'])
api.create_tag(NEW,repo_type='dataset',tag=TAG,revision=c.oid)
assert sha(anon('PILOT_MANIFEST.json'))==manifest_sha
for path in ['workspace/data/prepared/pilot/candidates/CHN/upr_response/train.sft.jsonl','workspace/data/prepared/pilot/candidates/DEU/upr_response/train.sft.jsonl']:
 e=next(e for e in entries if e['path']==path);assert sha(anon(path))==e['sha256']
receipt=dict(report,status='public_pilot_payload_verified',repo_id=NEW,private=False,commit=c.oid,tag=TAG,
 manifest_sha256=manifest_sha,remote_files_content_ids_verified=53,anonymous_sft_files_sha256_verified=2,
 combined_payload_files=15879,combined_payload_bytes=6778439838,verified_at=datetime.now(timezone.utc).isoformat())
save('publication.json',receipt)
print(json.dumps(receipt,indent=2),flush=True)
