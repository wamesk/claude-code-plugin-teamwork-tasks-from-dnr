"""Tests for the contract-task estimate (contract_estimate.py)."""
import contract_estimate as ce


def test_minimum_clamp():
    # 45 + 0 + 0 = 45 -> clamped up to 60.
    assert ce.estimate_minutes(0, 0) == 60


def test_typical():
    # 45 + 15*5 + 15*3 = 165.
    assert ce.estimate_minutes(5, 3) == 165


def test_maximum_clamp():
    assert ce.estimate_minutes(40, 40) == 480


def test_always_multiple_of_15():
    for endpoints in range(0, 20):
        for entities in range(0, 20):
            minutes = ce.estimate_minutes(endpoints, entities)
            assert minutes % 15 == 0
            assert 60 <= minutes <= 480


def test_negative_counts_are_floored():
    assert ce.estimate_minutes(-3, -1) == 60


def test_count_contract_surface():
    contract = {
        "openapi": {"endpoints": [{"method": "get"}, {"method": "post"}]},
        "data_model": {"entities": [{"name": "A"}]},
    }
    assert ce.count_contract_surface(contract) == (2, 1)


def test_estimate_from_contract():
    contract = {
        "openapi": {"endpoints": [{"method": "get"}] * 4},
        "data_model": {"entities": [{"name": "A"}, {"name": "B"}]},
    }
    # 45 + 15*4 + 15*2 = 135.
    assert ce.estimate_from_contract(contract) == 135
