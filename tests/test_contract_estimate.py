"""Tests for the contract-task estimate (contract_estimate.py)."""
import contract_estimate as ce


def test_minimum_clamp():
    # 30 + 0 + 0 = 30, the floor.
    assert ce.estimate_minutes(0, 0) == 30


def test_typical():
    # 30 + 7.5*5 + 7.5*3 = 90.
    assert ce.estimate_minutes(5, 3) == 90


def test_rounds_half_up():
    # 30 + 7.5 = 37.5 -> 45, not the banker's 30.
    assert ce.estimate_minutes(1, 0) == 45


def test_maximum_clamp():
    assert ce.estimate_minutes(40, 40) == 480


def test_always_multiple_of_15():
    for endpoints in range(0, 20):
        for entities in range(0, 20):
            minutes = ce.estimate_minutes(endpoints, entities)
            assert minutes % 15 == 0
            assert 30 <= minutes <= 480


def test_negative_counts_are_floored():
    assert ce.estimate_minutes(-3, -1) == 30


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
    # 30 + 7.5*4 + 7.5*2 = 75.
    assert ce.estimate_from_contract(contract) == 75
