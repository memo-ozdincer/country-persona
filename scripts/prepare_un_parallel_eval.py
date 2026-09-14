#!/usr/bin/env python3
"""Prepare the publisher's small dev/test sets; never emit training data."""
from collections import Counter
from pathlib import Path
import tarfile
from country_persona.acquire import download
from country_persona.io import write_json, write_jsonl, sha256

ROOT=Path('data/raw/expansion-20260913')
URL='https://www.un.org/dgacm/sites/www.un.org.dgacm/files/files/UNCORPUS/UNv1.0.testsets.tar.gz'

def main():
    archive=ROOT/'discovery/un_testsets.gz'
    download(URL,archive,source_id='un_testsets',max_bytes=50_000_000,expected_sha256='0b4040d723eab132fadc7809a329a4787b338a424ef23bfe3e029d41b7e0153d')
    archive_hash=sha256(archive)
    out=Path('data/prepared/expansion-20260913/un-parallel-eval')
    langs=['ar','en','es','fr','ru','zh'];stats={};docs={}
    with tarfile.open(archive) as tar:
        # Read named members directly: no archive extraction / path traversal.
        for name in ['README','DISCLAIMER']:
            target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(tar.extractfile('testsets/'+name).read())
        for split in ('dev','test'):
            prefix=f'testsets/{split}set/UNv1.0.{split}set'
            texts={lang:tar.extractfile(prefix+'.'+lang).read().decode('utf-8-sig').splitlines() for lang in langs}
            ids=tar.extractfile(prefix+'.ids').read().decode().splitlines()
            if any(len(lines)!=len(ids) for lines in texts.values()):raise ValueError('Parallel line count mismatch')
            rows=[];docs[split]=set()
            for i,identifier in enumerate(ids):
                document=identifier.split()[0];docs[split].add(document)
                if any(not texts[lang][i].strip() for lang in langs):raise ValueError('Empty parallel segment')
                rows.append(dict(id=f'unparallel:{split}:{i}',document_id=document,source_segment_ids=identifier,
                    group_id='unparallel:document:'+document,split=split,publisher_split=split,task='multilingual_evaluation_only',
                    country_iso3=None,represented_entity='UN_document_author_unspecified',
                    translations={lang:texts[lang][i] for lang in langs},source_url=URL,raw_file=str(archive),raw_sha256=archive_hash,
                    rights_status='publisher_disclaimer_and_attribution_terms_attached',training_admitted=False,
                    translation_status='publisher_manually_translated_aligned_corpus',quality_status='structural_checks_passed; semantic_review_pending'))
            write_jsonl(out/f'{split}.jsonl',rows)
            stats[split]=dict(aligned_segments=len(rows),language_rows=len(rows)*len(langs),documents=len(docs[split]))
    stats.update(languages=langs,shared_documents_between_publisher_dev_test=len(docs['dev']&docs['test']),
        training_rows=0,raw_bytes=archive.stat().st_size,raw_sha256=sha256(archive),
        interpretation='Institutional language/translation evaluation, not national stance supervision. Public data may overlap base-model pretraining.')
    write_json('reports/expansion-un-parallel.json',stats)
    print(stats)

if __name__=='__main__': main()
