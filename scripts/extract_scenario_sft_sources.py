"""Re-extract pinned official PDFs without altering historical source artifacts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def extract(pdf):
    import fitz
    if fitz.VersionBind != "1.26.7":
        raise ValueError("Use the pinned PDF audit runtime")
    doc = fitz.open(pdf)
    text, sections, coverage, edits = "", [], [], []
    for i, page in enumerate(doc):
        if tuple(page.rect) != (0, 0, 612, 792):
            raise ValueError("Unverified page geometry")
        parts = [("cover", page.rect)] if i == 0 else [
            ("left", fitz.Rect(50, 80, 307, 710)), ("right", fitz.Rect(307, 80, 563, 710))]
        if i:
            whole = Counter(w[4] for w in page.get_text("words", clip=fitz.Rect(50, 80, 563, 710)))
            split = Counter(w[4] for _, clip in parts for w in page.get_text("words", clip=clip))
            if whole != split:
                raise ValueError("Column word inventory mismatch")
            coverage.append({"page": i + 1, "body_words": sum(whole.values()), "equal": True})
        for column, clip in parts:
            raw = page.get_text("text", clip=clip, sort=True)
            # Retain printed hard hyphens; remove only their line-wrap whitespace.
            pattern = r"\u00ad\s*|(?<=\w)-[ \t]*\n[ \t]*(?=\w)"
            for m in re.finditer(pattern, raw):
                edits.append({"page": i + 1, "column": column, "raw_start": m.start(),
                              "raw_end": m.end(), "before": m.group(),
                              "after": "" if m.group().startswith("\u00ad") else "-",
                              "rule": "discretionary_hyphen" if m.group().startswith("\u00ad") else "printed_hyphen_wrap"})
            value = re.sub(pattern, lambda m: "" if m.group().startswith("\u00ad") else "-", raw)
            value = " ".join(value.split())
            if text:
                text += "\n\n"
            start = len(text)
            text += value
            sections.append({"page": i + 1, "column": column, "start": start,
                             "end": len(text), "raw_text": raw})
    return text, {"sections": sections, "coverage": coverage, "normalization_edits": edits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = []
    for number, parent in [("9214", "data/raw/source-plan-grounding-20261002-v1"),
                           ("8923", "data/raw/eval-sources-20260927"),
                           ("9138", "data/raw/eval-sources-20260927")]:
        pdf = Path(parent) / f"record-{number}.pdf"
        text, audit = extract(pdf)
        (args.output / f"record-{number}.txt").write_text(text)
        (args.output / f"record-{number}.extraction.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
        sources.append({"id": number, "pdf": str(pdf), "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                        "source": f"record-{number}.txt", "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                        "pages": len(audit["coverage"]) + 1,
                        "url": f"https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.{number}&t=pdf"})
    (args.output / "sources.json").write_text(json.dumps({"method": "PyMuPDF 1.26.7; sorted columns; whitespace normalization and reversible wrap ledger", "sources": sources}, indent=2) + "\n")


if __name__ == "__main__":
    main()
