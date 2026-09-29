"""Auditable speech extraction for the two-column UN records in the pilot."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .io import digest, sha256


def normalize(text):
    return " ".join(text.split())


def unique_span(text, quote):
    quote = normalize(quote)
    if not quote or text.count(quote) != 1:
        raise ValueError(f"Expected one occurrence of source anchor: {quote[:100]!r}")
    start = text.index(quote)
    return start, start + len(quote)


def extract_columns(pdf):
    """Coordinates were visually checked for these letter-size UN meeting records.

    Default pdftotext can interleave columns. Crop each body column independently,
    then concatenate left/right per page. Page 1 contains the cover, not speeches.
    Retain character ranges so every selected span maps back to a PDF page/column.
    """
    pdf = Path(pdf)
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    if not re.search(r"Page size:\s+612 x 792 pts", info):
        raise ValueError("This crop recipe is restricted to verified letter-size records")
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    sections, document = [], ""
    for page in range(2, pages + 1):
        for column, x, width in (("left", 54, 244), ("right", 310, 248)):
            command = ["pdftotext", "-f", str(page), "-l", str(page), "-r", "72",
                       "-x", str(x), "-y", "80", "-W", str(width), "-H", "630",
                       "-enc", "UTF-8", str(pdf), "-"]
            text = normalize(subprocess.check_output(command, text=True))
            if document:
                document += "\n\n"
            start = len(document)
            document += text
            sections.append({"page": page, "column": column, "start": start,
                             "end": len(document), "text": text})
    return {"pdf_sha256": sha256(pdf), "method": "pdftotext cropped columns v1",
            "crop_points": {"y": 80, "height": 630, "left": [54, 244], "right": [310, 248]},
            "text": document, "text_digest": digest(document), "sections": sections}


def extract_speech(document, spec, source):
    start, _ = unique_span(document["text"], spec["start_anchor"])
    end, _ = unique_span(document["text"], spec["end_anchor"])
    if start >= end:
        raise ValueError("Speech boundaries are reversed")
    if source["role"] != "prior_public_statement":
        raise ValueError("Outcome references and drafts cannot become prior speeches")
    text = document["text"][start:end].rstrip()
    end = start + len(text)
    locations = [{"page": s["page"], "column": s["column"],
                  "document_start": max(start, s["start"]), "document_end": min(end, s["end"])}
                 for s in document["sections"] if s["start"] < end and s["end"] > start]
    if sorted({x["page"] for x in locations}) != spec["pages"]:
        raise ValueError("Speech page boundaries differ from the visually checked inventory")
    return {"id": spec["id"], "country": spec["country"], "source_id": source["id"],
            "symbol": source["symbol"], "statement_date": source["document_date"],
            "source_role": source["role"], "pdf_sha256": source["sha256"],
            "source_url": source["url"], "document_text_digest": document["text_digest"],
            "document_start": start, "document_end": end, "locations": locations,
            "text": text, "text_digest": digest(text), "publication_before_vote_verified": False,
            "review_status": "assistant_source_checked; independent_review_pending"}


def locate_support(evidence, quote):
    """References point into exactly the evidence visible to arm B."""
    start, end = unique_span(evidence["text"], quote)
    absolute_start = evidence["document_start"] + start
    absolute_end = evidence["document_start"] + end
    locations = [{"page": s["page"], "column": s["column"]} for s in evidence["locations"]
                 if s["document_start"] < absolute_end and s["document_end"] > absolute_start]
    return {"evidence_id": evidence["id"], "start": start, "end": end,
            "quote": evidence["text"][start:end], "text_digest": evidence["text_digest"],
            "locations": locations}
