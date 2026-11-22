"""Replay a calendar clerk's read of the subsequent three actual UNAMI records."""
import json
from pathlib import Path

from handover import CROSS

path=CROSS/"colombia2023/peer-index-transfer-evidence/final-records.json"
records,=json.loads(path.read_text()).values()
source=json.loads((CROSS/"unami2023/case.json").read_text())["roles"]
assert "31 May 2024" in source["mandate desk"]["TERM"]
assert "31 March 2024" in source["review desk"]["REVIEW"]
assert "every four months" in source["mandate desk"]["REPORT"]
annotations={
    "unindexed":("extending the mandate of UNAMI to 31 May 2024","due no later than 31 March 2024",
                 "the resolution does not mandate biannual submissions","correct cadence omitted"),
    "indexed":("extending the mandate of UNAMI to 31 May 2024","a strategic review of UNAMI by 31 March 2024",
               "report biannually on the mission's fulfilment of responsibilities","incorrect cadence"),
    "no_question":("extending UNAMI's mandate to 31 May 2024","an independent strategic review of UNAMI by 31 March 2024",
                   "report biannually on UNAMI's fulfilment of responsibilities","incorrect cadence")
}
result={}
for arm,(term,review,cadence,status) in annotations.items():
    memo=records[f"unami/{arm}/final"]
    assert all(span in memo for span in (term,review,cadence))
    assert "four months" not in memo and "four-month" not in memo
    result[arm]={"term":term,"review":review,"reporting":cadence,"reporting_verdict":status,
                 "one_time_deadlines_correct":2,"all_three_calendar_entries_correct":False}
print(json.dumps(result,indent=2))
