# backend/tests/test_onchain_normalize_helpers.py

from app.adapters.onchain import _norm_alnum_upper, _age_hours_ms


def test_norm_alnum_upper_edges():
    assert _norm_alnum_upper("SoL-123") == "SOL123"
    assert _norm_alnum_upper("  ray_dium  ") == "RAYDIUM"
    assert _norm_alnum_upper("") == ""
    assert _norm_alnum_upper(None) == ""


def test_age_hours_ms_nonnegative_and_float():
    one_hour_ms = 60 * 60 * 1000
    age = _age_hours_ms(one_hour_ms)
    assert isinstance(age, float)
    # we only assert it's non-negative and roughly in range when the window is small
    assert age >= 0.0
