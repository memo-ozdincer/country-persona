"""Preserve generated acquisition manifests separately from Git-ignored source bytes."""
import json
import shutil
from pathlib import Path
from zipfile import ZipFile
from .io import sha256, write_json

COLLECTIONS={
    'mfa':'mfa/collection.json','china_mission':'china_mission/collection.json',
    'germany_mission':'germany_mission/sitemap_collection.json','germany_press':'germany_press/collection.json',
    'ungdc':'ungdc/collection.json','unbench':'unbench/collection.json',
}


def save_manifests(root=Path('.')):
    root=Path(root)
    for source,relative in COLLECTIONS.items():
        path=root/'data/raw'/relative
        if path.exists():
            data=json.loads(path.read_text())
            write_json(root/'data/manifests'/(source+'.json'),data)
    derived=[]
    archive=root/'data/raw/unga_speech_corpus/corpus.zip'
    if archive.exists():
        with ZipFile(archive) as z:
            for name in z.namelist():
                if name.startswith('UNGA Speech Corpus Data/') and name.endswith('.RData'):
                    path=archive.parent/Path(name).name
                    if path.exists():derived.append({'archive':str(archive),'member':name,'path':str(path),'sha256':sha256(path)})
    write_json(root/'data/derived_sources.json',derived)


def restore_generated_sources(root=Path('.')):
    root=Path(root)
    for source,relative in COLLECTIONS.items():
        source_path=root/'data/manifests'/(source+'.json');dest=root/'data/raw'/relative
        if source_path.exists() and not dest.exists():
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_path,dest)
    path=root/'data/derived_sources.json'
    if path.exists():
        for item in json.loads(path.read_text()):
            dest=root/item['path']
            if not dest.exists():
                with ZipFile(root/item['archive']) as z:
                    member=z.getinfo(item['member'])
                    if member.file_size>300_000_000:raise ValueError('Oversize archive member')
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(member) as src,dest.open('wb') as out:shutil.copyfileobj(src,out)
            if sha256(dest)!=item['sha256']:raise ValueError('Extracted source hash mismatch')
