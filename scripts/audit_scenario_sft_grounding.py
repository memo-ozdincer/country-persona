"""Compile the manually read curation into complete, replayable source maps."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from country_persona.io import read_jsonl, sha256, write_json
from country_persona.meeting_sequence import digest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release", type=Path, required=True)
    args = p.parse_args()
    release = args.release.resolve()
    if (release / "grounding.json").exists():
        raise ValueError("Preserve the earlier audit")
    curation = json.loads((release / "curation.json").read_text())
    pins = json.loads((release / "sources/sources.json").read_text())["sources"]
    texts, maps, audits = {}, {}, []
    for pin in pins:
        n = pin["id"]
        text = (release / "sources" / pin["source"]).read_text()
        audit = json.loads((release / f"sources/record-{n}.extraction.json").read_text())
        sections, values = audit["sections"], []
        for section in sections:
            raw = section["raw_text"]
            edits = [x for x in audit["normalization_edits"] if (x["page"], x["column"]) == (section["page"], section["column"])]
            for edit in reversed(edits):
                if raw[edit["raw_start"]:edit["raw_end"]] != edit["before"]:
                    raise ValueError("Normalization ledger offset mismatch")
                raw = raw[:edit["raw_start"]] + edit["after"] + raw[edit["raw_end"]:]
            value = " ".join(raw.split())
            if text[section["start"]:section["end"]] != value:
                raise ValueError("Normalization replay changed a PDF section")
            values.append(value)
        if "\n\n".join(values) != text or digest(text) != pin["source_sha256"] or sha256(ROOT / pin["pdf"]) != pin["pdf_sha256"]:
            raise ValueError("Changed full source or PDF")
        texts[n], maps[n] = text, sections
        audits.append(dict(source=n, pages=pin["pages"], body_pages=len(audit["coverage"]),
            body_word_inventories_equal=all(x["equal"] for x in audit["coverage"]),
            normalization_edits=len(audit["normalization_edits"]), normalization_replay_equal=True,
            source_sha256=pin["source_sha256"], pdf_sha256=pin["pdf_sha256"]))
    def reference(n, a, b):
        return dict(source=n, start=a, end=b, text_sha256=digest(texts[n][a:b]),
            locations=[dict(page=s["page"], column=s["column"], start=max(a, s["start"]), end=min(b, s["end"]))
                       for s in maps[n] if s["start"] < b and s["end"] > a])
    rows = [r for split in ("train", "eval") for r in read_jsonl(release / f"pack/{split}.jsonl")]
    cases, rubric = {}, {}
    for row in rows:
        n, prov = row["source"], row["provenance"]
        offset, _ = prov["window"]
        target = prov["turns"][-1]
        target_ref = reference(n, *prov["target"])
        scene_refs = []
        for quote in curation["scene_evidence"][n]:
            a = texts[n].index(quote)
            if a + len(quote) > offset + target["start"]:
                raise ValueError("Scenario evidence is not available before target")
            scene_refs.append({"quote": quote, **reference(n, a, a + len(quote))})
        segments = []
        for index, turn in enumerate(prov["turns"]):
            a, b = offset + turn["content_start"], offset + turn["end"]
            segments.append(dict(kind="target" if index == len(prov["turns"]) - 1 else "context",
                country=turn["country"], capacity=turn["capacity"], representative=turn["representative"],
                printed_header=reference(n, offset + turn["start"], a), body=reference(n, a, b)))
        cases[row["id"]] = dict(scene=scene_refs, segments=segments, target=target_ref,
            target_source_equal=texts[n][prov["target"][0]:prov["target"][1]] == row["body"],
            target_characters=len(row["body"]), target_sha256=row["target_sha256"],
            documentary_content="All supplied body characters are direct source spans; headers, phase labels, omission disclosures, markers and task instructions are authored metadata, adjudicated in curation.json.")
        if not cases[row["id"]]["target_source_equal"]:
            raise ValueError("Incomplete target grounding")
        units = []
        for uid, criterion, quote in curation["cases"][row["id"]]:
            if quote not in row["body"]:
                raise ValueError("Criterion navigator is not in the complete target")
            a = prov["target"][0] + row["body"].index(quote)
            units.append(dict(id=uid, criterion=criterion, navigator_quote=quote,
                navigator=reference(n, a, a + len(quote)), complete_support=target_ref))
        rubric[row["id"]] = units
    write_json(release / "grounding.json", dict(status="source_maps_and_normalization_replay_pass",
        curation_sha256=sha256(release / "curation.json"), sources=audits, cases=cases,
        independent_review_complete=False, production_model_calls=0, production_optimizer_updates=0))
    write_json(release / "rubric.json", dict(cases=rubric, guards={
        "source_faithfulness": "Read the entire answer. No unsupported substantive addition, altered numbers, missing modal qualification or fabricated hidden reasoning; disputed national assertions remain attributable.",
        "institutional_role": "Requested national delegation only; no borrowing another speaker's ownership, population-wide values or Council-president authority.",
        "chronology": "No invented subsequent vote, adoption, fulfilled pledge or future decision. Known earlier vote is allowed in sanctions reconstruction, not a forecasting score.",
        "output_integrity": "One readable complete speech, no runaway repetition, thought trace or other-speaker continuation. Inspect raw control tokens as well as display text; cap failure is not a pass."
    }, interpretation="Four fitting speeches are memorization controls. Two historically exposed Ukraine speeches are fit-excluded development transfer. Strict criterion coverage is not all possible valid diplomacy; source fidelity is not neutral factual truth.",
        independent_review_complete=False))
    write_json(release / "quality-review.json", dict(status="same_assistant_source_and_example_review_complete",
        curation_sha256=sha256(release / "curation.json"), grounding_sha256=sha256(release / "grounding.json"),
        rubric_sha256=sha256(release / "rubric.json"), pack_release_sha256=sha256(release / "pack/release.json"),
        selected_full_speeches=6, material_criteria=sum(map(len, rubric.values())),
        all_selected_documentary_bodies_fully_source_bound=True, all_scenario_anchors_precede_targets=True,
        independent_review_complete=False, production_model_calls=0, production_optimizer_updates=0))
    print(json.dumps({"sources": audits, "examples": len(cases), "criteria": sum(map(len, rubric.values()))}, indent=2))


if __name__ == "__main__":
    main()
