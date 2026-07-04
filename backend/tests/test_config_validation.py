import pytest

from config_validation import validate_runtime_config


def _clear_payment_env(monkeypatch):
    for name in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"):
        monkeypatch.delenv(name, raising=False)


def test_rejects_placeholder_jwt_secret(monkeypatch):
    _clear_payment_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "replace-with-a-long-random-secret")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_runtime_config()


def test_allows_no_razorpay_config_for_non_payment_dev(monkeypatch):
    _clear_payment_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a-real-local-secret-value")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ALLOW_TEST_BYPASS", "false")
    validate_runtime_config()


def test_rejects_partial_razorpay_config(monkeypatch):
    _clear_payment_env(monkeypatch)
    monkeypatch.setenv("JWT_SECRET", "a-real-local-secret-value")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_123")
    with pytest.raises(RuntimeError, match="Razorpay config is incomplete"):
        validate_runtime_config()


def test_rejects_invalid_razorpay_key_id(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "a-real-local-secret-value")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "bad_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret")
    with pytest.raises(RuntimeError, match="RAZORPAY_KEY_ID"):
        validate_runtime_config()
