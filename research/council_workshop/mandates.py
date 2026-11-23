"""Exact feasibility rules for workshops with a finite menu and private mandates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Mandates:
    options: dict[str, str]
    allowed: dict[str, frozenset[str]]

    @classmethod
    def from_case(cls, case, countries):
        config = case.get("mandate_game")
        if config is None:
            return None
        if not isinstance(config, dict) or not isinstance(config.get("allowed"), dict):
            raise ValueError("Supply a package menu and private mandates")
        options = config.get("options")
        if (not isinstance(options, dict) or not options
                or any(not isinstance(label, str) or not label or label != label.strip()
                       or not isinstance(text, str) or not text or text != text.strip()
                       for label, text in options.items())
                or len(set(options.values())) != len(options)
                or case["draft"] not in options.values()):
            raise ValueError("Supply unique, nonempty package labels and clauses, including the opening draft")
        legal = set(options)
        allowed = {}
        for country in countries:
            values = config["allowed"].get(country)
            if (not isinstance(values, list) or not all(isinstance(value, str) for value in values)
                    or len(values) != len(set(values)) or not set(values) <= legal):
                raise ValueError(f"Invalid mandate for {country}")
            allowed[country] = frozenset(values)
        return cls(options.copy(), allowed)

    def score(self, status, draft):
        feasible = sorted(set(self.options).intersection(*self.allowed.values()))
        selected = next(label for label, text in self.options.items() if text == draft)
        if status == "unanimous_acceptance":
            outcome = "valid_agreement" if selected in feasible else "invalid_agreement"
        elif status == "certified_impasse":
            if feasible:
                raise ValueError("A certified impasse cannot have a feasible package")
            outcome = status
        else:
            outcome = "unresolved"
        return {"feasible_packages": feasible, "selected_package": selected, "outcome": outcome,
                "reward": int(outcome in ("valid_agreement", "certified_impasse"))}
