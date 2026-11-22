"""Join the two-meeting vote packet to pinned UNSC-Bench and UNBench sources."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

import pyarrow.parquet as pq

from country_persona.unsc_bench import country_name, normalize_record

ROOT = Path(__file__).resolve().parents[4]
PACK = Path(__file__).with_name("facilitator-mixed-votes.json")


def verify():
    packet = json.loads(PACK.read_text())
    conferences = {record["id"]: (meeting["meeting"], record)
                   for meeting in packet.values() for record in meeting["records"]}
    ub = json.loads((ROOT / "data/manifests/unbench-full-20260926.json").read_text())
    uc = json.loads((ROOT / "data/manifests/unsc-bench-20260926.json").read_text())
    expected_names = {symbol.replace("/", "_") + "-EN.json": symbol for symbol in conferences}
    matches = {symbol: {"UNBench": [], "UNSC-Bench": []} for symbol in conferences}
    with ZipFile(ROOT / ub["file"]) as archive:
        for member in archive.namelist():
            name = Path(member).name
            if name in expected_names:
                symbol = expected_names[name]
                matches[symbol]["UNBench"].append({"path": member, "sha256": sha256(archive.read(member)).hexdigest()})
    for kind in ("adopted", "vetoed"):
        relative = f"{kind}/data.parquet"
        file = ROOT / uc["local_root"] / relative
        assert sha256(file.read_bytes()).hexdigest() == next(row["sha256"] for row in uc["files"] if row["path"] == relative)
        for index, row in enumerate(pq.ParquetFile(file).read().to_pylist()):
            item = normalize_record(row, kind, index)
            symbol = item["draft_symbol"]
            if symbol not in conferences:
                continue
            meeting, record = conferences[symbol]
            assert str(item["meeting"]).removeprefix("S/PV.") == meeting.removeprefix("S/PV.")
            source_votes = {country_name(actor): label
                            for group, label in (("yes", "Y"), ("no", "N"), ("abstain", "A"))
                            for actor in record[group]}
            assert {vote["country"]: vote["vote"] for vote in item["votes"]} == source_votes
            matches[symbol]["UNSC-Bench"].append({"split": kind, "row": index, "votes_match": 15,
                                                 "issues": item["issues"]})
    return {"packet_sha256": sha256(PACK.read_bytes()).hexdigest(),
            "unsc_bench_revision": uc["revision"], "matches": matches}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
