"""Acquire an explicit small PDF source list, retaining hashes and page boundaries."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import urllib.request

from country_persona.io import sha256, write_json


def collect(config, root):
    root.mkdir(parents=True, exist_ok=True)
    items = json.loads(config.read_text())["sources"]
    receipt_path = root / "acquisition.json"
    previous = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    previous_sources = {s["id"]: s for s in previous.get("sources", [])}
    receipts = []
    for item in items:
        path = root / (item["id"] + ".pdf")
        receipt = dict(item)
        try:
            cached = previous_sources.get(item["id"], {})
            if (path.exists() and cached.get("status") == "acquired" and
                cached.get("url") == item["url"] and cached.get("sha256") == sha256(path)):
                # Preserve the acquisition metadata on an unchanged cached rebuild.
                receipt = {**cached, **item}
            if not path.exists():
                request = urllib.request.Request(item["url"], headers={"User-Agent": "country-persona-research/0.1"})
                with urllib.request.urlopen(request, timeout=45) as response:
                    body = response.read(30_000_001)
                    receipt.update(final_url=response.url, content_type=response.headers.get("Content-Type"))
                if len(body) > 30_000_000 or not body.startswith(b"%PDF-"):
                    raise ValueError("Expected a PDF smaller than 30 MB, not a challenge/error page")
                temporary = path.with_suffix(".pdf.part")
                temporary.write_bytes(body)
                temporary.replace(path)
            text_path = path.with_suffix(".txt")
            # Keep both diagnostic views. Meeting-record speech spans are built
            # separately with the visually checked per-column extraction recipe.
            subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), str(text_path)], check=True)
            subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), str(path.with_suffix(".layout.txt"))], check=True)
            info = subprocess.check_output(["pdfinfo", str(path)], text=True)
            pages = int(next(line.split(":", 1)[1] for line in info.splitlines() if line.startswith("Pages:")))
            text = text_path.read_text()
            if item["symbol"] not in text or not text.strip():
                raise ValueError("Expected document symbol is absent from extracted text")
            receipt.update(status="acquired", path=str(path), sha256=sha256(path), bytes=path.stat().st_size,
                           pages=pages, text_path=str(text_path), text_sha256=sha256(text_path),
                           extraction="pdftotext default reading order; form-feed page boundaries preserved")
        except Exception as exc:
            receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        receipts.append(receipt)
        print(item["id"], receipt["status"], receipt.get("error", receipt.get("pages")), flush=True)
    payload = {"acquired_at": previous.get("acquired_at"),
               "source_config_sha256": sha256(config), "sources": receipts}
    if payload != previous:
        payload["acquired_at"] = datetime.now(timezone.utc).isoformat()
        write_json(receipt_path, payload)
    return receipts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    receipts = collect(args.config, args.root)
    if any(r["status"] != "acquired" for r in receipts):
        raise SystemExit(1)
