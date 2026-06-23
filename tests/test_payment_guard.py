import pytest
from fastapi import HTTPException

import settings
from dependencies import require_mock_payment_enabled


def test_mock_payment_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_MOCK_PAYMENT", False)

    with pytest.raises(HTTPException) as exc_info:
        require_mock_payment_enabled()

    assert exc_info.value.status_code == 403


def test_mock_payment_can_be_enabled_explicitly(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_MOCK_PAYMENT", True)

    assert require_mock_payment_enabled() is None
