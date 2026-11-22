"""Inspect complete criterion arrays in saved outputs, including capped prefixes."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def array_prefix(text):
    marker = text.find('"units"')
    if marker < 0:
        return
    cursor = text.find("[", marker) + 1
    if not cursor:
        return
    decoder = json.JSONDecoder()
    while True:
        remaining = text[cursor:].lstrip(" \n\r\t,")
        if not remaining.startswith("["):
            return
        try:
            value, n = decoder.raw_decode(remaining)
        except json.JSONDecodeError:
            return
        yield value
        cursor = len(text) - len(remaining) + n


def run():
    raw = HERE / "evidence/calls.jsonl"
    report = {}
    for line in raw.read_text().splitlines():
        call = json.loads(line)
        name, form = call["request"]["id"].split("/")
        if form != "quoted":
            continue
        data = json.loads(call["request"]["messages"][-1]["content"])
        source = data["sources"]
        record = data["record"]
        reply = call["response"]
        rows = []
        for unit in array_prefix(reply["text"]):
            if not isinstance(unit, list) or len(unit) != 5 or not all(isinstance(field, str) for field in unit):
                rows.append({"malformed_unit": unit})
                continue
            criterion, status, span, block, witness = unit
            row = {"id": criterion, "status": status}
            if status == "M":
                row.update(exact_record_span=bool(span.strip() and span in record),
                           exact_source_span=bool(block in source and witness.strip() and witness in source[block]))
                if not row["exact_record_span"]:
                    row["incorrect_record_span"] = span
                if not row["exact_source_span"]:
                    row["incorrect_source_span"] = {"block": block, "span": witness}
            rows.append(row)
        report[name] = {
            "termination": reply["termination"], "complete_unit_arrays": len(rows),
            "marked_met": sum(r.get("status") == "M" for r in rows),
            "met_with_record_quote_mismatch": sum(r.get("exact_record_span") is False for r in rows),
            "met_with_source_quote_mismatch": sum(r.get("exact_source_span") is False for r in rows),
            "units": rows,
        }
    return {"scope": "Post hoc diagnostic only. Capped or invalid replies remain inadmissible.",
            "quoted_calls": report, "calls_sha256": sha256(raw.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
