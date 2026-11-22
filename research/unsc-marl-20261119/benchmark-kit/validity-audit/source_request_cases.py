"""Evidence packets for the three-field source-recovery experiment."""
import json
from pathlib import Path

from source_record_run import digest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MINURSO = HERE / "source-record-minurso.json"
DPRK = HERE / "source-record-dprk-routing.json"
MALI = ROOT / "crossbench/mali/historical-task.json"


def read(path):
    return json.loads(path.read_text())


def piece(block, text, start=None):
    if start is not None:
        assert text.count(start) == 1
        text = text[text.index(start):].split(". ", 1)[0].rstrip(".") + "."
    return {"block": block, "quote": text}


def cases():
    minurso = read(MINURSO)["cases"][0]["delegate_evidence"]
    dz, ch = minurso["Algeria"], minurso["Switzerland"]
    dprk = read(DPRK)["cards"]
    mali = {x["id"]: x for x in read(MALI)["evidence"]}
    return {
        "western_sahara": {
            "weights": (14, 6, 4), "joint": (6, 4), "source": str(MINURSO.relative_to(ROOT)),
            "fields": (
                {"name": "Algerian monitoring position and non-participation reason",
                 "evidence": [piece("DZ-A", dz["DZ-A"]), piece("DZ-B", dz["DZ-B"])]},
                {"name": "Swiss second amendment vote and continuity rationale",
                 "evidence": [piece("CH-A", ch["CH-A"], "She said Switzerland abstained")]},
                {"name": "Swiss first amendment vote and access rationale",
                 "evidence": [piece("CH-A", ch["CH-A"], "After declaring that she was now speaking")]},
            ),
        },
        "dprk": {
            "weights": (10, 9, 5), "joint": (6, 4), "source": str(DPRK.relative_to(ROOT)),
            "fields": (
                {"name": "Japan's speaking capacity and assessment of the veto",
                 "evidence": [piece("JAPAN", dprk["JAPAN"]["text"])]},
                {"name": "China's abstention and consultations qualification",
                 "evidence": [piece("CHINA", dprk["CHINA"]["text"], "He explained that China abstained")]},
                {"name": "China's independent Panel and sanctions review positions",
                 "evidence": [piece("CHINA", dprk["CHINA"]["text"], "China’s Geng Shuang supported")]},
            ),
        },
        "mali": {
            "weights": (12, 10, 3), "joint": (3, 3), "source": str(MALI.relative_to(ROOT)),
            "fields": (
                {"name": "Co-penholders' peace-agreement and drawdown objectives",
                 "evidence": [piece("french-uae", mali["french-uae"]["text"])]},
                {"name": "Russia's final-extension and Panel dissolution position",
                 "evidence": [piece("russia", mali["russia"]["text"])]},
                {"name": "France's post-vote objection about the separate draft",
                 "evidence": [piece("france-after", mali["france-after"]["text"])]},
            ),
        },
    }


def hashes():
    return {str(p.relative_to(ROOT)): digest(p) for p in (MINURSO, DPRK, MALI, Path(__file__))}
