"""Check whether either locked UNSC-Bench split contains the joined event."""
from hashlib import sha256
import json

import pyarrow.parquet as pq

import facilitator_resolution_2719 as study


def coverage():
    root = study.provenance.audit.archive.ROOT
    manifest = json.loads((root / "data/manifests/unsc-bench-20260926.json").read_text())
    identity = study.packet()["event"]
    tokens = (identity["meeting"], identity["draft"], "S/RES/2719", "S_RES_2719", "S_PV.9518", "S_2023_999")
    out = {}
    for row in manifest["files"]:
        if not row["path"].endswith("data.parquet"):
            continue
        file = root / manifest["local_root"] / row["path"]
        actual = sha256(file.read_bytes()).hexdigest()
        assert actual == row["sha256"]
        split = row["path"].split("/")[0]
        rows = pq.ParquetFile(file).read().to_pylist()
        matches = []
        for i, item in enumerate(rows):
            normalized = study.provenance.audit.normalize_record(item, split, i)
            exact = (normalized.get("meeting") == identity["meeting"] or
                     normalized.get("draft_symbol") == identity["draft"])
            text = json.dumps(item, default=str)
            aliases = [t for t in tokens if t in text]
            if exact or aliases:
                matches.append({"row": i, "identifier_match": exact, "tokens_in_row": aliases})
        out[split] = {"rows": len(rows), "matches": matches, "sha256": actual}
    return {"revision": manifest["revision"], "event": identity, "splits": out}


if __name__ == "__main__":
    print(json.dumps(coverage(), indent=2))
