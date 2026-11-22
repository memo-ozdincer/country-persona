"""Repeat the reader measurements on the records as actually delivered."""
import json
import os
from pathlib import Path
from unittest.mock import patch

import pilot


def assembled():
    archive=json.loads(pilot.ARCHIVE.read_text())["cases"]
    for r in original():
        arms=archive[r["family"]]["same_batch"]
        if r["arm"] not in arms: continue
        anchor=arms[r["arm"]]
        assert anchor["record"].endswith(anchor["supplement"])
        assert r["prompt"].count(anchor["supplement"])==1
        yield dict(r,prompt=r["prompt"].replace(anchor["supplement"],anchor["record"]))


original=pilot.dataset
if __name__=="__main__":
    directory=Path("assembled-evidence")
    os.environ["CUDA_VISIBLE_DEVICES"]=""
    with patch.object(pilot,"dataset",lambda:list(assembled())):
        pilot.run(directory)
    (directory/"wrapper.sha256").write_text(pilot.sha256(Path(__file__).read_bytes()).hexdigest()+"\n")
