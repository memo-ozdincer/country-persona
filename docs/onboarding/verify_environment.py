"""Inspect installed version metadata only; no CUDA or model initialization."""
import argparse
import importlib.metadata
import json
import platform


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['cpu', 'gpu'], required=True)
    args = parser.parse_args()
    expected = {'torch': '2.8.0+cpu' if args.profile == 'cpu' else '2.8.0+cu128',
                'transformers': '5.17.0', 'trl': '1.14.1', 'peft': '0.21.1',
                'datasets': '5.0.1', 'accelerate': '1.15.0'}
    actual = {name: importlib.metadata.version(name) for name in expected}
    mismatch = {k: {'expected': v, 'actual': actual[k]} for k, v in expected.items() if actual[k] != v}
    required_python = (3, 11) if args.profile == 'cpu' else (3, 12)
    if tuple(map(int, platform.python_version_tuple()[:2])) != required_python:
        mismatch['python'] = {'expected_major_minor': required_python, 'actual': platform.python_version()}
    if mismatch:
        raise SystemExit(json.dumps({'status': 'profile_mismatch', 'differences': mismatch}, indent=2))
    print(json.dumps({'status': 'version_metadata_matches', 'profile': args.profile,
                      'python': platform.python_version(), 'versions': actual,
                      'scope': 'Package metadata only; no CUDA, model loading or training test.'}, indent=2))


if __name__ == '__main__':
    main()
