from app.adapters.onchain import _norm_alnum_upper, _age_hours_ms
import time

def test_onchain_helper_norm_and_age_time_correct():
    assert _norm_alnum_upper("SoL-123") == "SOL123"
    assert _norm_alnum_upper(None) == ""
    assert _norm_alnum_upper("") == ""
    three_hours_ms = 3 * 60 * 60 * 1000
    now_ms = int(time.time() * 1000)
    ts_ms = now_ms - three_hours_ms
    age = _age_hours_ms(ts_ms)
    assert isinstance(age, float)
    assert abs(age - 3.0) < 0.5
