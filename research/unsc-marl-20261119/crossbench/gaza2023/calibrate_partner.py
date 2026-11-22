"""Exact budgeted calibration against unfamiliar deterministic requester schedules."""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

import routing

HERE = routing.HERE
HORIZONS = (1, 8, 32)
BUDGET = 6
PROBE_FEE = .05
ZERO = (0,) * 4


def read(name):
    return json.loads((HERE / name).read_text())


def source_digest(name):
    return routing.digest(HERE / name)


class Calibration:
    def __init__(self):
        self.priors = dict(routing.priors())
        self.development_priors = read("prior-blind-results.json")["training_priors"]
        self.design_prior = np.mean([self.priors[name] for name in self.development_priors], axis=0)
        self.points = np.asarray(read("compiled-results.json")["scores_by_focus_and_receipt"])
        self.fitted_sender, self.fitted_receiver = map(np.asarray, read("routing-fit.json")["learned_policy"])
        bounds = read("routing-results.json")["results"]["correlated_development"]["policies"]["exact_interactive"]
        self.exact_sender = np.asarray(bounds["sender"])
        self.question_loss, self.reply_loss, self.question_fee, self.reply_fee = routing.config()

    def probabilities(self, state):
        # -1 records a seen request. Other values count observed silences.
        ratio = self.question_loss ** np.maximum(np.asarray(state), 0)
        return np.where(np.asarray(state) == -1, 1., ratio / (1 + ratio))

    def utility(self, probabilities, receiver, prior):
        receiver = np.asarray(receiver)
        focus = np.arange(4)[:, None]
        arrived = (1 - self.question_loss) * probabilities[:, None]
        on_target = arrived * (receiver[:, 1] == focus) + (1 - arrived) * (receiver[:, 0] == focus)
        base = self.points[:, 0] @ prior.sum(axis=1)
        gained = (self.points[:, 1] - self.points[:, 0]) @ (prior * on_target).sum(axis=1)
        fees = self.question_fee * (prior.sum(axis=1) @ probabilities) + self.reply_fee
        return float(base + (1 - self.reply_loss) * gained - fees)

    def receiver(self, probabilities, prior):
        arrived = (1 - self.question_loss) * probabilities
        mass = prior.T[:, None, :] * np.stack([1 - arrived, arrived])[None, :, :]
        mass *= self.points[:, 1] - self.points[:, 0]
        return np.where(routing.OPTIONS[:, None, :], mass, -1.).argmax(axis=-1)

    @lru_cache(maxsize=None)
    def terminal(self, state, mode):
        probability = self.probabilities(state)
        if mode == "flip_only":
            pair = [self.fitted_receiver, self.fitted_receiver[:, ::-1]]
            value = [self.utility(probability, table, self.design_prior) for table in pair]
            idx = int(np.argmax(value))
            return pair[idx], value[idx]
        table = self.receiver(probability, self.design_prior)
        return table, self.utility(probability, table, self.design_prior)

    def branches(self, state, action, probability):
        if state[action] == -1:
            return ((1., state),)
        observed_request = (1 - self.question_loss) * probability
        outcomes = []
        for q, fraction in enumerate([1 - observed_request, observed_request]):
            updated = list(state)
            updated[action] = -1 if q else state[action] + 1
            outcomes.append((fraction, tuple(updated)))
        return outcomes

    @lru_cache(maxsize=None)
    def select(self, state, left, horizon, mode):
        value = horizon * self.terminal(state, mode)[1]
        best = (value, None)
        if left == 0:
            return best
        for action, probability in enumerate(self.probabilities(state)):
            if state[action] == -1:
                continue
            expected = -PROBE_FEE - self.question_fee * probability
            for chance, next_state in self.branches(state, action, probability):
                expected += chance * self.select(next_state, left - 1, horizon, mode)[0]
            if expected > best[0] + 1e-12:
                best = (expected, action)
        return best

    def replay(self, sender, horizon, mode):
        scores = dict.fromkeys(self.priors, 0.0)
        cost = probes = 0.0

        def visit(state, left, probability):
            nonlocal cost, probes
            if mode == "frozen":
                table, action = self.fitted_receiver, None
            elif mode == "blind":
                table, action = self.terminal(ZERO, "flexible")[0], None
            elif mode == "one_each":
                # Fixed public deck. All four topic probes are always attempted.
                table = self.terminal(state, "flexible")[0]
                action = BUDGET - left if BUDGET - left < 4 else None
            else:
                table = self.terminal(state, mode)[0]
                _, action = self.select(state, left, horizon, mode)
            if action is None:
                for name, prior in self.priors.items():
                    scores[name] += probability * self.utility(sender, table, prior)
                return
            q = sender[action]
            cost += probability * (PROBE_FEE + self.question_fee * q)
            probes += probability
            for chance, next_state in self.branches(state, action, q):
                if chance:
                    visit(next_state, left - 1, probability * chance)

        visit(ZERO, BUDGET, 1.)
        return {"calibration_rounds": probes, "calibration_cost": cost,
                "net_scores": {name: score - cost / horizon for name, score in scores.items()}}


def summarize(rows, train):
    same_info = [row["known_sender_design_prior"]["net_scores"][train] for row in rows]
    return {method: {"mean_net": float(np.mean([row[method]["net_scores"][train] for row in rows])),
                     "worst_gap_to_known_sender": min(row[method]["net_scores"][train] - ceiling
                                                      for row, ceiling in zip(rows, same_info, strict=True)),
                     "mean_calibration_rounds": float(np.mean([row[method]["calibration_rounds"] for row in rows]))}
            for method in rows[0]}


def run():
    calibration = Calibration()
    terminal_names = ("frozen", "blind", "one_each", "flip_only", "flexible")
    matched = (calibration.fitted_sender, calibration.exact_sender)
    hashes = ["compiled-results.json", "routing-fit.json", "routing-results.json", "prior-blind-results.json"]
    out = {}
    for horizon in HORIZONS:
        entries = {}
        for sender in routing.REQUESTS:
            fields = {mode: calibration.replay(sender, horizon, mode) for mode in terminal_names}
            decoder = calibration.receiver(sender, calibration.design_prior)
            for oracle, prior_informed in (("known_sender_design_prior", False), ("known_sender_informed", True)):
                calibrated = {name: calibration.utility(sender, calibration.receiver(sender, prior) if prior_informed
                                                         else decoder, prior)
                              for name, prior in calibration.priors.items()}
                fields[oracle] = {"calibration_rounds": 0., "calibration_cost": 0., "net_scores": calibrated}
            entries["".join(map(str, sender))] = fields

        train = "correlated_development"
        known = {"fitted": "".join(map(str, matched[0])), "exact": "".join(map(str, matched[1]))}
        unfamiliar = [row for key, row in entries.items() if key not in known.values()]
        design_average = np.mean([entries["".join(map(str, q))]["flexible"]["net_scores"][name]
                                  for q in routing.REQUESTS for name in calibration.development_priors])
        expected, first = calibration.select(ZERO, BUDGET, horizon, "flexible")
        assert np.isclose(expected / horizon, design_average)
        # Independent archived evaluator check with an attainable 28-point backup in every focus.
        sender, receiver = calibration.fitted_sender, calibration.fitted_receiver
        check_prior = calibration.priors[train]
        actual = calibration.points.copy()
        calibration.points[:, 1] = 70
        assert np.isclose(calibration.utility(sender, receiver, check_prior),
                          routing.measure(check_prior, sender, receiver)["net"])
        calibration.points[:, :] = actual
        out[str(horizon)] = {"first_adaptive_probe": first, "named_senders": known,
                             "other_schedules_on_development_prior": summarize(unfamiliar, train),
                             "by_sender": entries}
    return {"scope": "One public calibration probe names a dummy focus. The desk emits its usual bit with the "
                     "original question loss. Neither real inventory nor evaluation prior is disclosed. Decoder design "
                     "uses the mean of four development priors and a uniform prior over all 16 deterministic senders. "
                     "Metrics include the probe fee and actual attempted-request fee amortized over the declared missions.",
            "source_digests": {name: source_digest(name) for name in hashes}, "code_sha256": routing.digest(Path(__file__)),
            "probe_fee": PROBE_FEE, "probe_cap": BUDGET, "results": out}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
