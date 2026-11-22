"""Cross the fitted and exact training partners with the deployed question channel."""
import json

import numpy as np

import routing


def report():
    fit_path = routing.HERE / "routing-fit.json"
    bounds_path = routing.HERE / "routing-results.json"
    fit = json.loads(fit_path.read_text())
    assert fit["baseline_sha256"] == routing.digest(bounds_path)
    bounds = json.loads(bounds_path.read_text())
    reference = bounds["results"][fit["training_prior"]]["policies"]["exact_interactive"]
    trained = [np.asarray(x) for x in fit["learned_policy"]]
    exact = [np.asarray(reference[k]) for k in ("sender", "receiver")]
    assert np.array_equal(trained[0], 1 - exact[0])
    modes = {"fitted_pair": trained, "exact_pair": exact,
             "fitted_requester_exact_responder": (trained[0], exact[1]),
             "exact_requester_fitted_responder": (exact[0], trained[1]),
             "fitted_requester_inverted_exact_responder": (trained[0], exact[1][:, ::-1]),
             "exact_requester_inverted_fitted_responder": (exact[0], trained[1][:, ::-1])}
    priors = {name: {mode: routing.measure(prior, *policy) for mode, policy in modes.items()}
              for name, prior in routing.priors()}
    return {"scope": "Crossplay uses two policies fit or optimized on the same development prior. XOR aligns the "
                     "responder's two message labels using the observed codebooks. It leaves physical erasure as "
                     "silence and does not imply general calibration on new partners.",
            "fit_sha256": routing.digest(fit_path), "exact_sha256": routing.digest(bounds_path), "scores": priors}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
