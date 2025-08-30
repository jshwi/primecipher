import base64
import json

import pytest
from app.api.routes.parents import _dec_cursor
from fastapi import HTTPException


def test_dec_cursor_invalid_base64_raises():
    with pytest.raises(HTTPException) as e:
        _dec_cursor("not-base64!")
    assert e.value.status_code == 400


def test_dec_cursor_negative_offset_raises():
    bad = base64.urlsafe_b64encode(json.dumps({"o": -5}).encode()).decode()
    with pytest.raises(HTTPException) as e:
        _dec_cursor(bad)
    assert e.value.status_code == 400
