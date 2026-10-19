"""Matched application control with explicit permission for recommendations."""
import json
from pathlib import Path
import run_grounded_role_checkpoint as runner

runner.PACK=runner.ROOT/"research/native-plan-writer-application-20261019-v1"
runner.FIT=runner.ROOT/"runs/native-plan-writer-resume-20261019-v1"

if __name__=="__main__":
    actual=json.loads((runner.ROOT/"research/native-plan-writer-20261019-v1/config.json").read_text())
    old=json.loads((runner.ROOT/"research/scenario-role-sft-20261017-v1/fit-config.json").read_text())
    assert all(actual[k]==old[k] for k in ["model","revision","model_path"])
    runner.main()
