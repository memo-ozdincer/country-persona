import argparse
import json
from pathlib import Path
from .io import write_json


def main():
    p=argparse.ArgumentParser(description='Country persona data workbench')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('normalize');sub.add_parser('inventory')
    q=sub.add_parser('fetch');q.add_argument('--lock',required=True)
    q=sub.add_parser('build');q.add_argument('--config',default='configs/pilot.json');q.add_argument('--canonical',default='data/canonical');q.add_argument('--output',default='data/prepared/pilot');q.add_argument('--families')
    q=sub.add_parser('audit');q.add_argument('input');q.add_argument('--verify-raw',action='store_true');q.add_argument('--output')
    q=sub.add_parser('admit');q.add_argument('--data',required=True);q.add_argument('--manifest',required=True);q.add_argument('--ledger',required=True);q.add_argument('--output',required=True)
    q=sub.add_parser('index');q.add_argument('--input',required=True);q.add_argument('--output',required=True)
    q=sub.add_parser('retrieve');q.add_argument('--index',required=True);q.add_argument('--query',required=True);q.add_argument('--before',required=True);q.add_argument('--exclude-group',required=True);q.add_argument('--country');q.add_argument('--limit',type=int,default=5)
    a=p.parse_args()
    if a.command=='normalize':
        from .pipeline import normalize
        result=normalize()
    elif a.command=='inventory':
        from .audit import source_inventory
        result=source_inventory()
    elif a.command=='fetch':
        from .acquire import fetch_lock
        result=fetch_lock(a.lock)
        write_json('reports/fetch_result.json',result)
        if result['failures']:raise SystemExit('Some downloads failed; see reports/fetch_result.json')
    elif a.command=='build':
        from .prepare import build
        result=build(a.config,a.canonical,a.output,a.families)
    elif a.command=='audit':
        from .audit import audit
        result=audit(a.input,a.verify_raw)
        if a.output:write_json(a.output,result)
        if result['errors']:print(json.dumps(result,indent=2));raise SystemExit(1)
    elif a.command=='admit':
        from .prepare import admit
        result=admit(a.data,a.manifest,a.ledger,a.output)
    elif a.command=='index':
        from .retrieval import create_index
        result=create_index(a.input,a.output)
    else:
        from .retrieval import search
        result=search(a.index,a.query,a.before,a.exclude_group,a.country,a.limit)
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
