"""Apply the same 2744 scoring contract to a frozen and adapted chair."""
import json
from unittest.mock import patch

from train_writer import HERE, HOLD, read, plan

import score as original


def run():
    spec=plan()
    assert spec==read(HERE/"plan.json")
    captured=read(HERE/"verified.json")["outputs"]
    marks=read(HERE/"marks.json")
    reference=read(HOLD/"plan.json")
    historical=read(HOLD/"verified.json")["outputs"]
    assert reference["requests"]==spec["held"]
    results={}
    for mode, output in captured.items():
        replacements={"plan.json":reference,"verified.json":{"outputs":output},"marks.json":marks[mode]}

        def project(path):
            if path.parent==HERE and path.name in replacements:
                return replacements[path.name]
            return read(path)

        with patch.object(original,"HERE", HERE), patch.object(original,"plan",return_value=reference), patch.object(
                original,"read",side_effect=project):
            results[mode]=original.run()
    return {"frozen_text_matches_archived":{key:row["text"]==historical[key]["text"]
                                            for key,row in captured["frozen"].items()},
            "semantic_marks":marks,"scores":results}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
