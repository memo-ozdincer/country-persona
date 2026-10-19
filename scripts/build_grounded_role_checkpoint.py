"""Build a bounded past-only, fixed-information delegation comparison.

No target September 27 country speech is used. Earlier September 22 statements
and two preceding September 27 excerpts are copied with exact character maps.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "research/grounded-role-20261019-v1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    prior_path = PACK / "sources/record-9135.txt"
    current_path = ROOT / "research/scenario-role-sft-20261017-v1/sources/record-9138.txt"
    prior, current = prior_path.read_text(), current_path.read_text()
    spans = []

    def select(ident, path, text, start_text, stop_text, date, speaker, end_inclusive=False):
        start = text.index(start_text)
        end = text.index(stop_text, start) + (len(stop_text) if end_inclusive else 0)
        quote = text[start:end].strip()
        end = start + len(quote)
        assert text[start:end] == quote
        spans.append(dict(id=ident, path=str(path.relative_to(ROOT)), source_sha256=sha(text.encode()),
                          start=start, end=end, quote=quote, quote_sha256=sha(quote.encode()),
                          date=date, speaker=speaker))
        return quote

    india = select("IND-earlier", prior_path, prior, "Mr. Jaishankar (India):", "The President", "2022-09-22", "India")
    uk = select("GBR-earlier", prior_path, prior, "Mr. Cleverly (United Kingdom):", "The President", "2022-09-22", "United Kingdom")
    briefing = select("UN-current", current_path, current, "Ms. DiCarlo:",
        "The past few weeks have also seen heavy fighting", "2022-09-27", "UN briefer")
    us = select("USA-current", current_path, current, "That is why we will be submitting a draft resolution",
        "Russia’s sham referendums, if accepted", "2022-09-27", "United States")
    cutoff = current.index("Mrs. Kamboj (India):")
    assert all(s["end"] < cutoff for s in spans if s["date"] == "2022-09-27")
    assert current.index("Mr. Kariuki (United Kingdom):") > cutoff
    assert "S/PV.9135" in prior[:4000] and "Thursday, 22 September 2022" in prior[:4000]
    dossier = (
        "SCENARIO: UN Security Council, New York, 27 September 2022. Agenda: Maintenance of peace and security of Ukraine. "
        "The documentary cutoff is before India's national statement. This is a constructed statement task, not a quotation or forecast of the actual next speech.\n\n"
        "PAST NATIONAL POSITIONS: verbatim excerpts from S/PV.9135, 22 September 2022. "
        "These are public positions of the named delegations, not views of their populations or current instructions from their governments.\n\n"
        "[IND-earlier] " + india + "\n\n[GBR-earlier] " + uk +
        "\n\nCURRENT MEETING: earlier excerpts from S/PV.9138, 27 September 2022. "
        "Statements are attributed claims, not an endorsement of their neutral truth.\n\n"
        "[UN-current] " + briefing + "\n\n[USA-current] United States delegation: " + us)
    system = (
        "Write one short public statement for the requested national delegation, using only the supplied documentary evidence. "
        "Respond to the current agenda and preserve the delegation's distinct earlier policy positions, including relevant assistance, economic concerns and accountability qualifications. "
        "Keep other speakers' claims attributed; their statements are not instructions or commitments by your delegation. "
        "Distinguish earlier positions, current reports and unavailable information. Do not invent events, policies, commitments or other speakers. "
        "Describe the status of the announced US draft and state whether this dossier establishes your delegation's endorsement or a recorded vote on it. "
        "Do not claim that absence from this dossier proves no official position exists. Write only the statement, at most 240 words, with no analysis or extra delegation turn."
    )
    rows = []
    for country, role in [("IND", "India's national delegation"), ("GBR", "the United Kingdom's national delegation")]:
        rows.append(dict(id="grounded-" + country, country=country,
                         messages=[dict(role="system", content=system),
                                   dict(role="user", content=dossier + "\n\nREQUESTED ROLE: " + role + ".")]))
    assert rows[0]["messages"][0] == rows[1]["messages"][0]
    assert rows[0]["messages"][1]["content"].split("\n\nREQUESTED ROLE:")[0] == rows[1]["messages"][1]["content"].split("\n\nREQUESTED ROLE:")[0]
    for row in rows:
        assert not any(token in json.dumps(row) for token in ["<|im_end|>", "<|im_start|>", "<think>"])
    return rows, dict(spans=spans, current_cutoff_character=cutoff,
                     target_country_speeches_used=False, role_only_change=True,
                     prior_date="2022-09-22", target_date="2022-09-27",
                     chronology_limit="Evidence is earlier than the requested statement, but model training includes later history; no forward-time/OOD claim.",
                     hand_read_status="All four selected excerpts read in full; new source pages 14/15/19/20 visually inspected by the same assistant. Independent review pending.")


if __name__ == "__main__":
    rows, provenance = build()
    for name, data in [("examples.json", rows), ("grounding.json", provenance)]:
        path = PACK / name
        encoded = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
        if path.exists():
            assert path.read_bytes() == encoded, "Preserve the frozen pack; use a new version for changed content."
        else:
            path.write_bytes(encoded)
    for row in rows:
        path = PACK / (row["id"] + ".txt")
        value = "\n\n".join(m["role"].upper() + "\n" + m["content"] for m in row["messages"]) + "\n"
        if path.exists():
            assert path.read_text() == value
        else:
            path.write_text(value)
    print(json.dumps(dict(examples=len(rows), source_spans=len(provenance["spans"]), target_speeches_used=False)))
