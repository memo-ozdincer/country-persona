"""Score the numbered source records and replay the frozen communication policies."""
import argparse
import json
from unittest.mock import patch

import numbered as w
import population

n, e = w.n, w.e
CHECKLIST = {
    "brazil-reason": ("brazil", {"6", "8"}, "Brazil explains operational freedom and partial accommodation."),
    "china-reason": ("china", {"7", "5"}, "China links inadequate accommodation with its emphasis on sovereignty and consent."),
    "russia-reason": ("russia", {"9", "2"}, "Russia links contentious late changes and the lost compromise to abstention, and supports the mission."),
}
PUBLIC_MARKS = {
    "procedure": ("vote", "Names the date, draft and sponsor."),
    "disposition": ("vote", "Gives the adopted resolution and full vote tally with abstainers."),
    "duration": ("operative", "Gives the mandate end date."),
    "permission": ("operative", "Gives independence in mandated tasks without prior permission."),
    "coordination": ("operative", "Gives continued coordination with Lebanon's Government under the status-of-forces agreement."),
}


def grade_records():
    _, case_source, _ = n.setup()
    visible = case_source["evidence"]
    sources = {item["id"]: item["text"] for item in visible}
    case = {"id": case_source["id"], "task": case_source["task"], "rubric": case_source["rubric"],
            "track": "historical", "word_cap": n.LIMIT, "public": visible, "owned": []}
    bank = w.records()
    assessed = {}
    for arm, records in bank["records"].items():
        assessed[arm] = {}
        for mask, record in records.items():
            calls = [{}, {}, {"text": record["text"], "termination": "complete"}]
            packet = e.final_packet(case, calls)
            paragraphs = record["text"].split("\n\n")
            used = record["used"]

            def grade(unit, meets, response, blocks, reason):
                return {"id": unit, "status": "met" if meets else "unmet",
                        "response": response if meets else "", "source": [
                            {"block": name, "quote": sources[name]} for name in blocks
                        ] if meets else [], "reason": reason if meets else "The complete item is absent."}

            marks = [grade(unit, True, paragraphs[0], (block,), reason)
                     for unit, (block, reason) in PUBLIC_MARKS.items()]
            for unit, (role, ids, reason) in CHECKLIST.items():
                text = next((p for p in paragraphs if p.startswith(role.title() + " — ")), "")
                marks.append(grade(unit, ids <= set(used[role]), text, (role,), reason))
            present = all(ids <= set(used[role]) for role, ids in w.COMPARE.items())
            orphaned_qualification = "8" in used["brazil"] and "6" not in used["brazil"]
            marks.extend((
                grade("overlap", present, paragraphs[-1], ("brazil", "china"), "Names shared support for UNIFIL's work."),
                grade("open-issue", present and not orphaned_qualification, "\n\n".join(paragraphs[1:]), ("brazil", "china"),
                      "Links Brazil's partial accommodation to China's judgment that accommodation was insufficient."),
            ))
            # Documentary reading of the bounded renderer. Vote and mandate prose uses audited
            # spans, every role sentence is quoted, and the comparison is worded at the supported scope.
            guard = {"status": "clear", "response": "", "source": [],
                     "reason": "Each quoted passage retains its named speaker and the comparison stays on the matched issue."}
            if orphaned_qualification:
                span = w.MENUS["brazil"]["8"]
                guard = {"status": "uncertain", "response": span,
                         "source": [{"block": "brazil", "quote": sources["brazil"]}],
                         "reason": "The quoted while-clause omits the verb phrase that told the reader what Brazil assessed."}
            data = {"id": packet["id"], "units": marks, "guard": guard}
            assessed[arm][mask] = {"packet": packet, "marks": data, "score": e.final_score(case, calls, data)}
    return {"selection": bank["selection"], "rendered": bank["records"], "assessed": assessed}


def replay(scored):
    result = {}
    for arm, records in scored["assessed"].items():
        rows = {int(mask): row["score"] for mask, row in records.items()}
        points = {mask: row["released_70"] for mask, row in rows.items()}
        read = population.n.read

        def load(path):
            if path == population.b.HERE / "results.json":
                return {"records": {str(k): v for k, v in rows.items()}}
            return read(path)

        with patch.object(population.n, "read", load):
            model = population.run()
        result[arm] = {"records": rows, "selected_states": n.comparison(points), "population": model}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("grades", "replay"))
    mode = parser.parse_args().mode
    e.emit(grade_records() if mode == "grades" else replay(json.loads((w.HERE / "grades.json").read_text())))
