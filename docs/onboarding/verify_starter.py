"""Check clone-accessible saved evidence with standard Python; never load a model.

Optional --extract writes the 130 exact embedded text artifacts into a fresh
directory. It does not restore adapter binaries, PDFs or the complete snapshot.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Evidence(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.data = ''
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'evidence':
            self.active = True
    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False
    def handle_data(self, value):
        if self.active:
            self.data += value


def verify():
    parser = Evidence()
    parser.feed((ROOT / 'docs/evidence/minimal-country-sft-20261021/viewer.html').read_text())
    bundle = json.loads(parser.data)
    files = bundle['source_files']
    for name, record in files.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe embedded path')
        raw = record['text'].encode('utf-8')
        if sha(raw) != record['sha256'] or len(raw) != record['bytes']:
            raise ValueError('Embedded file bytes differ: ' + name)
    total = 0
    for run in bundle['runs'].values():
        for output, review in zip(run['outputs'], run['review']['reviews'], strict=True):
            if output['id'] != review['id'] or sha(output['output'].encode()) != review['output_sha256']:
                raise ValueError('Answer/review mismatch')
            total += 1
    if total != 94:
        raise ValueError('Missing saved answers')
    cases = [c for c in bundle['packs']['eight']['cases.jsonl']
             if c['family'] not in ('exact_control', 'strong_checked_plan_control')]
    scores = {}
    for arm, expected in [('extension-base', (23, 7)), ('extension-four', (34, 15)), ('extension-eight', (38, 15))]:
        reviews = {r['id']: r for r in bundle['runs'][arm]['review']['reviews']}
        content = sum(g['status'] == 'met' for c in cases for g in reviews[c['id']]['ratings'].values())
        application = sum(reviews[c['id']]['ratings'][u]['status'] == 'met' for c in cases
                          for u in ['scenario_application', 'commitment_boundary'])
        if (content, application) != expected:
            raise ValueError('Stored score arithmetic differs')
        scores[arm] = {'content': f'{content}/40', 'application_and_commitment': f'{application}/16'}
    receipt = json.loads((ROOT / 'docs/evidence/github-export-verification.json').read_text())
    for name, entry in receipt['pages'].items():
        if sha((ROOT / name).read_bytes()) != entry['sha256']:
            raise ValueError('Generated evidence page differs: ' + name)
    return bundle, {'status': 'clone_accessible_saved_evidence_verified', 'embedded_original_text_files': len(files),
                    'saved_answer_records': total, 'training_examples': 8,
                    'generated_evidence_pages': len(receipt['pages']), 'scores': scores,
                    'scope': 'Byte bindings and original score arithmetic; no new semantic judgment or model execution.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path, help='Fresh output directory for exact embedded original text files')
    args = parser.parse_args()
    bundle, report = verify()
    if args.extract is not None:
        destination = args.extract.absolute()
        if destination.exists():
            raise ValueError('Extraction destination must not exist')
        destination.mkdir(parents=True)
        for name, entry in bundle['source_files'].items():
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(entry['text'].encode('utf-8'))
        report['extracted_text_files'] = len(bundle['source_files'])
        report['extraction_directory'] = str(destination)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
