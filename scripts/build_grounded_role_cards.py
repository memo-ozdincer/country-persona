"""Compact exact-quote source cards after inspecting the full-dossier failure.

Preserves task, role switch, rubric and decoder. All card text is a substring of
the already audited earlier source; excluded narrative is recorded, not erased.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "research/grounded-role-20261019-v1"
OUT = ROOT / "research/grounded-role-cards-20261019-v1"


def build():
    prior = json.loads((PARENT / "grounding.json").read_text())
    originals = json.loads((PARENT / "examples.json").read_text())
    old = {s["id"]: s for s in prior["spans"]}
    spans = []

    def excerpt(ident, start, stop):
        source = old[ident]
        text = source["quote"]
        begin = text.index(start)
        end = text.index(stop, begin) + len(stop)
        quote = text[begin:end]
        spans.append(dict(parent_span=ident, path=source["path"], start=source["start"]+begin,
                          end=source["start"]+end, quote=quote,
                          source_sha256=source["source_sha256"], quote_sha256=hashlib.sha256(quote.encode()).hexdigest()))
        return quote

    india = [
        excerpt("IND-earlier", "Allow me to preface", "a member of the International Criminal Court."),
        excerpt("IND-earlier", "In a globalized world", "struggling global economy."),
        excerpt("IND-earlier", "That is why India strongly reiterates", "economic stress."),
        excerpt("IND-earlier", "Turning to the specific topic", "an independent investigation into the Bucha incident."),
        excerpt("IND-earlier", "The global order to which", "upheld without exception.")]
    uk = [
        excerpt("GBR-earlier", "They undertook to refrain", "any State."),
        excerpt("GBR-earlier", "Yet seven months ago", "without justification."),
        excerpt("GBR-earlier", "We have information", "refuse to recognize any results."),
        excerpt("GBR-earlier", "As members of the Security Council", "regional and global stability."),
        excerpt("GBR-earlier", "We will therefore stand", "no country is truly secure.")]
    common = originals[0]["messages"][1]["content"].split("\n\nPAST NATIONAL POSITIONS:")[0]
    common += ("\n\nPAST NATIONAL POSITIONS: compact verbatim source cards from S/PV.9135, 22 September 2022. "
               "Each quoted bullet belongs only to its named delegation; shared principles may be shared. "
               "These are public institutional positions, not population beliefs or fresh government instructions.\n\n"
               "INDIA | national delegation | 22 September 2022 | Mr. Jaishankar\n" +
               "\n".join("- " + s for s in india) +
               "\n\nUNITED KINGDOM | national delegation | 22 September 2022 | Mr. Cleverly\n" +
               "\n".join("- " + s for s in uk) +
               "\n\nCURRENT MEETING: earlier excerpts from S/PV.9138, 27 September 2022. "
               "Statements remain attributed claims, not neutral verified world truth.\n\n"
               "[UN-current] " + old["UN-current"]["quote"] +
               "\n\n[USA-current] United States delegation: " + old["USA-current"]["quote"])
    rows = []
    for row in originals:
        role = row["messages"][1]["content"].split("\n\nREQUESTED ROLE:")[1]
        rows.append({**row, "messages": [row["messages"][0], dict(role="user", content=common+"\n\nREQUESTED ROLE:"+role)]})
    for span in spans:
        assert (ROOT/span["path"]).read_text()[span["start"]:span["end"]] == span["quote"]
    for key in ["UN-current", "USA-current"]:
        spans.append(old[key])
    return rows, dict(parent_grounding_sha256=hashlib.sha256((PARENT/"grounding.json").read_bytes()).hexdigest(),
        spans=spans, new_historical_facts=False, target_country_speeches_used=False,
        current_cutoff_character=prior["current_cutoff_character"], role_only_change=True,
        intervention="Relevant earlier literal quotes shortened and grouped under explicit country ownership; not a pure length-only or instruction-only contrast.",
        removed_narrative="Greeting, nuclear anxiety/Modi anecdote, terrorism aside, UK casualty/atrocity statistics and individual victim story; original full dossier retained.")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=False)
    rows, grounding = build()
    for name, data in [("examples.json", rows), ("grounding.json", grounding)]:
        (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    (OUT/"rubric.json").write_bytes((PARENT/"rubric.json").read_bytes())
    for row in rows:
        (OUT/(row["id"]+".txt")).write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+"\n")
    print(json.dumps(dict(examples=len(rows), exact_source_spans=len(grounding["spans"]))))
