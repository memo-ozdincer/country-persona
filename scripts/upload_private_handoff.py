"""Upload a verified handoff to an explicitly private repository; credentials stay local."""
import argparse
import base64
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def verified_assets(archive, receipt, commit, asset_manifest=None):
    """Bind either a single asset or ordered split assets to the verified full archive."""
    bound=json.loads(receipt.read_text())
    archive_hash=sha256(archive)
    if bound['archive_sha256']!=archive_hash or bound['base_commit']!=commit or not bound['archive_payload_verified']:
        raise ValueError('Archive receipt/hash/commit binding differs')
    if bound.get('archive_bytes',archive.stat().st_size)!=archive.stat().st_size:
        raise ValueError('Archive receipt byte count differs')
    if asset_manifest is None:
        assets=[archive,receipt]
    else:
        manifest=json.loads(asset_manifest.read_text())
        if manifest['archive_name']!=archive.name or manifest['archive_sha256']!=archive_hash or manifest['archive_bytes']!=archive.stat().st_size:
            raise ValueError('Multipart manifest/full archive binding differs')
        parts=manifest['parts'];assets=[];names=set();combined=hashlib.sha256();total=0
        if not parts:raise ValueError('Multipart manifest has no parts')
        for part in parts:
            name=part['name']
            if Path(name).name!=name or name in names:raise ValueError('Part names must be unique local filenames')
            path=asset_manifest.parent/name
            if path.is_symlink() or not path.is_file():raise ValueError('Part must be a regular local file')
            size=path.stat().st_size
            if size!=part['bytes'] or not 0<size<2**31:raise ValueError('Part byte count or GitHub asset limit differs')
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);combined.update(block);total+=len(block)
            if h.hexdigest()!=part['sha256']:raise ValueError('Multipart part digest differs')
            names.add(name);assets.append(path)
        if combined.hexdigest()!=archive_hash or total!=archive.stat().st_size:
            raise ValueError('Ordered multipart reassembly differs from the verified archive')
        assets.extend([asset_manifest,receipt])
    if len({p.name for p in assets})!=len(assets):raise ValueError('Upload asset names must be unique')
    if any(p.stat().st_size>=2**31 for p in assets):raise ValueError('Split assets below the GitHub 2GiB limit before upload')
    return assets


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--tag',required=True);p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--body-file',type=Path,help='Exact release description; default preserves the historical objective-checkpoint description.')
    p.add_argument('--asset-manifest',type=Path,help='Ordered split-archive parts and full archive hashes; verified before creating a release.')
    args=p.parse_args()
    if args.output.exists():raise ValueError('Fresh upload receipt required')
    assets=verified_assets(args.archive,args.receipt,args.commit,args.asset_manifest)
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    values=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    auth=base64.b64encode((values['username']+':'+values['password']).encode()).decode()
    headers={'Authorization':'Basic '+auth,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    repository='memo-ozdincer/country-persona'
    api='https://api.github.com/repos/'+repository

    def request(url,method='GET',data=None,extra=None):
        h={**headers,**(extra or {})}
        body=json.dumps(data).encode() if isinstance(data,dict) else data
        if isinstance(data,dict):h['Content-Type']='application/json'
        with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=h,method=method),timeout=300) as response:
            return json.load(response)

    repo=request(api)
    if repo['full_name']!=repository or repo['private'] is not True:raise ValueError('Destination must be the verified private research repository')
    body=args.body_file.read_text() if args.body_file else 'Private verified research handoff: matched clause-weighted SFT and source-audited preference checkpoint. Includes frozen data, complete outputs, provisional reviews, measured/verification receipts and preserved failed attempts. Credentials and base weights excluded. No independent persona or multi-agent gain claimed.'
    release=request(api+'/releases','POST',{'tag_name':args.tag,'target_commitish':args.commit,'name':args.tag,
        'body':body,'draft':False,'prerelease':True})
    record={'state':'private_handoff_uploaded_and_remote_digests_verified','repository':repository,'private':True,'commit':args.commit,'tag':args.tag,
        'release_id':release['id'],'url':release['html_url'],'created_at':release['created_at'],'assets':[]}
    upload=release['upload_url'].split('{')[0]
    if not upload.startswith('https://uploads.github.com/repos/'+repository+'/releases/'):
        raise ValueError('Unexpected upload endpoint')
    for file in assets:
        expected=sha256(file)
        with file.open('rb') as stream:
            asset=request(upload+'?'+urllib.parse.urlencode({'name':file.name}),'POST',stream,
                {'Content-Type':('application/gzip' if file.suffix=='.gz' else 'application/json' if file.suffix=='.json' else 'application/octet-stream'),'Content-Length':str(file.stat().st_size)})
        verified=request(api+'/releases/assets/'+str(asset['id']))
        if verified['digest']!='sha256:'+expected or verified['size']!=file.stat().st_size:
            raise ValueError('Uploaded asset digest/size differs')
        record['assets'].append({'id':asset['id'],'name':file.name,'bytes':file.stat().st_size,'sha256':expected,
            'remote_digest_verified':True,'url':asset['browser_download_url']})
        print(json.dumps({'uploaded':file.name,'remote_digest_verified':True}),flush=True)
    record['verified_at']=datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(record,indent=2)+'\n')
    print(record['url'],flush=True)


if __name__=='__main__':main()
