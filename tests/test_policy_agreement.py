import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("compare_policy_reviewers", Path(__file__).parents[1] / "scripts/compare_policy_reviewers.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_complete_disagreement_has_negative_kappa():
    result = module.agreement(["met", "unmet"], ["unmet", "met"])
    assert result["raw_agreement"] == 0
    assert result["cohen_kappa"] == -1


def test_unknowns_are_visible_not_counted_as_agreement():
    result = module.agreement(["met", "unratable", "unmet"], ["met", "unratable", "unratable"])
    assert result["units"] == 3 and result["jointly_ratable"] == 1
    assert result["coverage"] == pytest.approx(1 / 3)
    assert result["raw_agreement"] == 1 and result["cohen_kappa"] is None


def test_no_ratable_units_is_not_perfect_agreement():
    result = module.agreement(["unratable"], ["unratable"])
    assert result["coverage"] == 0 and result["raw_agreement"] is None
