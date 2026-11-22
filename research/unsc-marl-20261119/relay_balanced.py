"""Check whether equal agreement and impasse exposure fixes raw-sign decisions."""
from dataclasses import dataclass
from fractions import Fraction
import json
from math import lcm
from pathlib import Path
from unittest.mock import patch

import relay_raw_signs as ablation

baseline=ablation.baseline
GENERATE=baseline.generate


@dataclass(frozen=True)
class Samples:
    task: baseline.Task
    worlds: tuple

    def __getattr__(self, name):
        return getattr(self.task,name)


def balanced(seed):
    buckets=[[],[]]
    originals=GENERATE(seed)
    for task in originals:
        for impasse in (False,True):
            subset=tuple((a,b) for a,b in task.worlds if (not (a&b))==impasse)
            if subset:
                buckets[int(impasse)].append(Samples(task,subset))
    # Preserve the public domains. Only which true worlds are presented to
    # the optimizer changes. Neither delegate receives the class bit.
    width=lcm(*(len(pool) for pool in buckets))
    return [pool[i%len(pool)] for i in range(width) for pool in buckets]


def probability(tasks):
    return sum(Fraction(sum(not(a&b) for a,b in task.worlds),len(task.worlds))
               for task in tasks)/len(tasks)


def run(raw_results):
    archive=json.loads(Path(raw_results).read_text())
    prior=probability(GENERATE(baseline.SEED))
    assert probability(balanced(baseline.SEED))==Fraction(1,2)
    with patch.object(baseline,"chair_rows",new=ablation.raw_signs),patch.object(
            baseline,"generate",new=balanced):
        fitted=baseline.cross_validate()
        transfer=ablation.judge_weights(fitted)
    return {"scope":"Same typed relay, action limits, raw-sign observation and update budget. The training menus are drawn from the same synthetic generator, with equal expected agreement and impasse exposure.",
            "expected_training_impasse_share":{"original":float(prior),"balanced":.5},
            "results":fitted,"large_transfer":transfer,
            "unbalanced_reference":{
                "small":{k:v["after"] for k,v in archive["same_fixture_holdout"]["arms"].items()},
                "large":archive["larger_linked_families"]["raw_signs"]}}


if __name__=="__main__":
    import sys

    print(json.dumps(run(sys.argv[1]),indent=2))
