"""Select an admitted-evidence policy using only a public channel declaration."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import facilitator_channel_fit as fit


def select(public, prior, opener, opening, estimate, candidates, conservative):
    # Compare policies using identical opening receipts and public evidence
    # eligibility. A failed reply is charged in each hypothetical regime.
    base = candidates["independent"]
    if conservative and estimate is not fit.PERFECT:
        plausible = (estimate, *fit.REGIMES[2:])
    else:
        plausible = (estimate,)
    baseline = [fit.measure(base, opener, opening, prior, public, mode)["net"] for mode in plausible]
    uplifts = {}
    for name, tail in candidates.items():
        deltas = [fit.measure(tail, opener, opening, prior, public, mode)["net"] - score
                  for mode, score in zip(plausible, baseline, strict=True)]
        uplifts[name] = min(deltas)
    # On ties keep the independent option, which is first in the mapping.
    picked = max(candidates, key=uplifts.__getitem__)
    return picked, uplifts


def run(path):
    replay = json.loads(path.read_text())
    afghanistan, _ = fit.measured_afghanistan()
    archives = fit.OLD.base.cases()[1]
    archives["resolution_2593"] = (fit.live.rubric(), fit.live.rubric())
    families = {}
    for family, (public, observed) in archives.items():
        families[family] = {}
        conditions = ({"source_only": fit.PERFECT, "question_visible": afghanistan}
                      if family == "resolution_2593" else fit.STRESS)
        for label in fit.live.PRIORS:
            prior = fit.ROUTE.TEST_PRIORS[label]
            opener, opening = fit.context(public, prior)
            families[family][label] = {}
            for name, actual in conditions.items():
                profiles = {"declared": fit.PERFECT if actual is fit.PERFECT else fit.DESIGN}
                if actual is not fit.PERFECT:
                    profiles["mistakenly_clean"] = fit.PERFECT
                else:
                    profiles["mistakenly_noisy"] = fit.DESIGN
                output = {}
                for profile, estimate in profiles.items():
                    plans = {
                        "independent": fit.exact(public, opening, estimate, independent=True),
                        "clean_fit": fit.action_policy(replay["clean"], public, opening, fit.PERFECT),
                        "initial_adapted": fit.action_policy(fit.OLD.INITIAL, public, opening, estimate),
                        "robust_fit": fit.action_policy(replay["robust"], public, opening, estimate),
                    }
                    output[profile] = {}
                    for selection in ("public_mean", "conservative"):
                        pick, uplift = select(public, prior, opener, opening, estimate, plans,
                                              selection == "conservative")
                        metrics = fit.measure(plans[pick], opener, opening, prior, observed, actual)
                        output[profile][selection] = {"picked": pick, "declared_uplift_by_policy": uplift, **metrics,
                                                      "expected_requests": float(opening.sum((0, 1)) @ (plans[pick][0] != 0))}
                families[family][label][name] = output
    return {"results": families, "sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                                           for p in (Path(__file__), Path(fit.__file__), path)}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit_report", type=Path)
    print(json.dumps(run(cli.parse_args().fit_report), indent=2))
