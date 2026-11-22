"""Reload the learned policies and compare every held-out action and delivery."""
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch

import torch

import relay_marl as common
import relay_raw_signs as ablation


def check_run(report, features):
    checked=0
    with patch.object(common,"chair_rows",new=features),torch.no_grad():
        for arm,table in report["arms"].items():
            torch.manual_seed(common.SEED)
            actor=common.Actor()
            for stage in ("before","after"):
                if stage=="after":
                    actor.load_state_dict({k:torch.tensor(v) for k,v in table["weights"].items()})
                for family,task in common.fixtures().items():
                    for control,stored in table[stage][family].items():
                        config=dict(channel=control,greedy=True)
                        if control=="truthful_relay":
                            config={"script":True}
                        computed=[common.rollout(actor,task,world,**config)[0] for world in task.worlds]
                        assert json.loads(json.dumps(computed))==stored
                        checked += len(stored)
            logs=table["updates"]
            assert [event["update"] for event in logs]==list(range(1,report["updates"]+1))
            assert all(math.isfinite(event["grad_norm"]) and event["grad_norm"]>0 for event in logs)
    return checked


def verify(folder):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    reads={}
    for key,sub in (("original","results"),("raw","raw"),("balanced","balanced")):
        launch="launch" if key=="original" else f"{key}-launch"
        record=json.loads((folder/f"{launch}.json").read_text())
        assert record["torch"]==torch.__version__
        for filename,expected in record["sha256"].items():
            assert sha256((common.HERE/filename).read_bytes()).hexdigest()==expected,filename
        artifact=json.loads((folder/f"{sub}.json").read_text())
        if key=="original":
            tested=artifact
        elif key=="raw":
            tested=artifact["same_fixture_holdout"]
            with patch.object(common,"chair_rows",new=ablation.raw_signs):
                restored=ablation.judge_weights(tested)
            assert json.loads(json.dumps(restored))==artifact["larger_linked_families"]["raw_signs"]
        else:
            tested=artifact["results"]
            with patch.object(common,"chair_rows",new=ablation.raw_signs):
                restored=ablation.judge_weights(tested)
            assert json.loads(json.dumps(restored))==artifact["large_transfer"]
        reads[key]={"episodes_replayed":check_run(
            tested,ablation.ORIGINAL if key=="original" else ablation.raw_signs),
            "input_files":len(record["sha256"]),"observations":"exact"}
    return reads


if __name__=="__main__":
    print(json.dumps(verify(Path(sys.argv[1])),indent=2))
