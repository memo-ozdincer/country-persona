"""Replay pinned new sources; existing bulk data and previous split ledgers are prerequisites."""
import json
from pathlib import Path
from country_persona.acquire import download
from country_persona.io import sha256, write_json

ROOT = Path('data/raw/country-extension-20260914')


def main():
    lock = json.loads(Path('data/manifests/country-extension-20260914.json').read_text())
    for ledger in lock['previous_split_ledgers']:
        if not Path(ledger['path']).exists() or sha256(ledger['path']) != ledger['sha256']:
            raise ValueError('Restore the prior release split ledger first: ' + ledger['path'])
    for item in lock['documents']:
        if item['status'] == 'acquired':
            download(item['url'], item['raw_file'], source_id=item['source_id'],
                     expected_sha256=item['raw_sha256'], max_bytes=80_000_000)
    context = lock['context_collection']
    for item in [context['observations']] + context['metadata']:
        download(item['url'], item['raw_file'], source_id=item['source_id'],
                 expected_sha256=item['sha256'], max_bytes=5_000_000)
    # Acquisition results retain their original snapshot metadata; any new
    # download receipt separately records this replay's actual retrieval time.
    write_json(ROOT / 'collection.json', {'registry': 'data/country_extension_registry.json',
                                        'documents': lock['documents']})
    write_json(ROOT / 'context/collection.json', context)
    print('Pinned new document and context sources verified. Run the preparation and curation scripts next.')


if __name__ == '__main__':
    main()
