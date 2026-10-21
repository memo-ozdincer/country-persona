"""Verify explicitly downloaded private release files; optionally reassemble v47.

No network, credentials, extraction, deletion or overwrite. Reassembly requires
a fresh output filename and uses the pinned part order, never a filename glob.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True, help='Key in artifacts.json')
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--assemble', type=Path, help='Fresh filename for the v47 whole archive')
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name('artifacts.json').read_text())
    release = manifest['releases'][args.release]
    verified = []
    for asset in release['assets']:
        if Path(asset['name']).name != asset['name']:
            raise ValueError('Unsafe manifest filename')
        path = args.directory / asset['name']
        if path.is_symlink() or not path.is_file() or path.stat().st_size != asset['bytes']:
            raise ValueError('Missing or wrong-sized asset: ' + asset['name'])
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != asset['sha256']:
            raise ValueError('Asset hash differs: ' + asset['name'])
        verified.append(asset['name'])
    if args.assemble is not None:
        if args.release != 'snapshot-v47':
            raise ValueError('Only snapshot-v47 has multipart assembly')
        multipart = json.loads(Path(__file__).with_name('v47-multipart.json').read_text())
        combined = hashlib.sha256()
        total = 0
        with args.assemble.open('xb') as output:
            for part in multipart['parts']:
                if part['name'] not in verified:
                    raise ValueError('Unverified part')
                with (args.directory / part['name']).open('rb') as stream:
                    for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                        output.write(block)
                        combined.update(block)
                        total += len(block)
        if combined.hexdigest() != multipart['archive_sha256'] or total != multipart['archive_bytes']:
            raise ValueError('Combined archive differs; preserve the failed output for inspection')
    print(json.dumps({'status': 'downloaded_assets_verified', 'release': args.release,
                      'assets': verified, 'assembled_archive': str(args.assemble) if args.assemble else None}, indent=2))


if __name__ == '__main__':
    main()
