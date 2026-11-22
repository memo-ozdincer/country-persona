"""Replay both frozen written-vote agents and equal-protocol scripts on the DRC packets."""
from importlib.util import module_from_spec, spec_from_file_location
import json

import results

source = results.HERE.parent / "haiti2023/policy_replay.py"
spec = spec_from_file_location("haiti_policy_controls", source)
policy = module_from_spec(spec)
spec.loader.exec_module(policy)

if __name__ == "__main__":
    run = policy.run()
    run["scope"] = ("First-pass DRC writer transfer. Both written-vote policies are frozen. Scripts use the true prior "
                    "and optimize reply order under the authored score. All use the same observed packet records.")
    print(json.dumps(run, indent=2, ensure_ascii=False))
