"""Locate the witness contrast documents in the pinned benchmark releases."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

import pyarrow.parquet as pq

from country_persona.unsc_bench import normalize_record

ROOT = Path(__file__).resolve().parents[4]
PACK = Path(__file__).with_name("facilitator-witness-contrast-packet.json")


def report():
    events = json.loads(PACK.read_text())
    lookup = {v["draft"]: k for k, v in events.items()}
    unbench = json.loads((ROOT / "data/manifests/unbench-full-20260926.json").read_text())
    unsc = json.loads((ROOT / "data/manifests/unsc-bench-20260926.json").read_text())
    names = {key.replace("/", "_") + "-EN.json": family for key, family in lookup.items()}
    result = {k: {"UNBench_drafts": [], "UNSC_Bench": []} for k in events}
    with ZipFile(ROOT / unbench["file"]) as archive:
        for member in archive.namelist():
            tag = names.get(Path(member).name)
            if tag:
                result[tag]["UNBench_drafts"].append(
                    {"path": member, "sha256": sha256(archive.read(member)).hexdigest()})
    for kind in ("adopted", "vetoed"):
        path = f"{kind}/data.parquet"
        file = ROOT / unsc["local_root"] / path
        assert sha256(file.read_bytes()).hexdigest() == next(row["sha256"] for row in unsc["files"] if row["path"] == path)
        for index, row in enumerate(pq.ParquetFile(file).read().to_pylist()):
            item = normalize_record(row, kind, index)
            family = lookup.get(item["draft_symbol"])
            if family:
                result[family]["UNSC_Bench"].append(
                    {k: item[k] for k in ("row_index", "config", "meeting", "date", "issues")})
    return {"packet_sha256": sha256(PACK.read_bytes()).hexdigest(),
            "UNSC_Bench_revision": unsc["revision"], "joins": result}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
