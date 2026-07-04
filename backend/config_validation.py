"""Runtime configuration checks that must pass before serving traffic."""
from __future__ import annotations

import os

PLACEHOLDER_JWT_SECRETS = {
    "",
    "change-me",
    "changeme",
    "secret",
    "your-secret-key",
    "corpintel-dev-secret",
    "replace-with-a-long-random-secret",
}

RAZORPAY_KEY_ID_PREFIXES = ("rzp_test_", "rzp_live_")


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _is_production_env() -> bool:
    value = (os.getenv("ENV") or os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "").strip().lower()
    return value in {"prod", "production"}


def validate_runtime_config():
    jwt_secret = os.getenv("JWT_SECRET", "")
    if not jwt_secret.strip() or jwt_secret.strip().lower() in PLACEHOLDER_JWT_SECRETS:
        raise RuntimeError(
            "JWT_SECRET must be set to a strong, non-placeholder value before startup."
        )
    if _is_production_env() and _env_bool("ALLOW_TEST_BYPASS"):
        raise RuntimeError(
            "ALLOW_TEST_BYPASS=true is not allowed when ENV/APP_ENV/ENVIRONMENT is production."
        )
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    has_any_razorpay = bool(key_id or key_secret or webhook_secret)
    if has_any_razorpay and not (key_id and key_secret and webhook_secret):
        raise RuntimeError(
            "Razorpay config is incomplete; set RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, and RAZORPAY_WEBHOOK_SECRET."
        )
    if key_id and not key_id.startswith(RAZORPAY_KEY_ID_PREFIXES):
        raise RuntimeError("RAZORPAY_KEY_ID must start with rzp_test_ or rzp_live_.")
