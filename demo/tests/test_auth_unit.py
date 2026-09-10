import pytest
from fastapi import HTTPException

from auth import OPERATOR_ENV, configured_operator_key, require_operator


def test_default_operator_key():
    assert configured_operator_key() == "dev-operator-key"


def test_operator_key_from_env(monkeypatch):
    monkeypatch.setenv(OPERATOR_ENV, "from-env")
    assert configured_operator_key() == "from-env"


def test_require_operator_rejects_missing():
    with pytest.raises(HTTPException) as exc:
        require_operator(None)
    assert exc.value.status_code == 401
