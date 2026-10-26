"""Build UNSC-Bench label variants from UNSC-Bench-Clean data and a corrections file.

  original/  unchanged copies of the Clean data
  corrected/ 'corrections' applied (votes and totals updated); flagged rows kept as-is
  excluded/  every row named in 'corrections' or 'flags' removed

The source data is never modified. Each variant gets a manifest with input hashes.
"""
import argparse, collections, hashlib, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = Path(os.environ.get('UNSC_BENCH_CLEAN_DATA', '/home/agokrani/UNSC-Bench-Clean/data'))
DEFAULT_CORR = ROOT / 'data' / 'curation' / 'unsc_bench_label_corrections_20261026.json'
FILES = ['vetoed_drafts.jsonl', 'nonvetoed_resolutions.jsonl']


def key_of(fname, row):
    return row['veto_id'] if fname == 'vetoed_drafts.jsonl' else row['identifiers']['symbol']


def apply(fname, row, fixes):
    votes = row['votes_by_member'] if fname == 'vetoed_drafts.jsonl' else row['member_state_votes']
    name = 'country' if fname == 'vetoed_drafts.jsonl' else 'name'
    for f in fixes:
        hit = [v for v in votes if v[name] == f['country']]
        assert len(hit) == 1 and hit[0]['vote'] == f['original'], (f, hit)
        hit[0]['vote'] = f['corrected']
    c = collections.Counter(v['vote'] for v in votes)
    if fname == 'vetoed_drafts.jsonl':
        row['total_yes'], row['total_no'], row['total_abstentions'] = c['Y'], c['N'], c['A']
    else:
        vt = row['voting_totals']
        vt['vote_yes'], vt['vote_no'], vt['vote_abstention'] = c['Y'], c['N'], c['A']
    row.setdefault('_label_corrections', []).extend(fixes)


def build(src, corr, out):
    doc = json.loads(corr.read_text())
    fixes = collections.defaultdict(list)
    for c in doc['corrections']:
        fixes[(c['file'], c['key'])].append(c)
    drop = set(fixes) | {(f['file'], f['key']) for f in doc['flags'] if f.get('action') == 'exclude'}

    for variant in ['original', 'corrected', 'excluded']:
        d = Path(out) / variant
        d.mkdir(parents=True, exist_ok=True)
        counts = {}
        for fname in FILES:
            kept = []
            for line in (src / fname).open():
                if not line.strip():
                    continue
                row = json.loads(line)
                k = (fname, key_of(fname, row))
                if variant == 'corrected' and k in fixes:
                    apply(fname, row, fixes[k])
                if variant == 'excluded' and k in drop:
                    continue
                kept.append(row)
            with (d / fname).open('w') as f:
                for row in kept:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
            counts[fname] = len(kept)
        manifest = {'variant': variant, 'corrections_version': doc['version'],
                    'corrections_sha256': hashlib.sha256(corr.read_bytes()).hexdigest(),
                    'source_sha256': {f: hashlib.sha256((src / f).read_bytes()).hexdigest() for f in FILES},
                    'rows': counts}
        (d / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        print(variant, counts)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True)
    ap.add_argument('--data-dir', type=Path, default=DEFAULT_SRC)
    ap.add_argument('--corrections', type=Path, default=DEFAULT_CORR)
    args = ap.parse_args()
    build(args.data_dir, args.corrections, args.out)


if __name__ == '__main__':
    main()
