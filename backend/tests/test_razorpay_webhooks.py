import importlib
import sys
import types


class _FakeUtility:
    def verify_webhook_signature(self, payload, signature, secret):
        if payload != '{"ok": true}' or signature != "sig" or secret != "whsec":
            raise ValueError("invalid signature")


class _FakeClient:
    def __init__(self, auth):
        self.auth = auth
        self.utility = _FakeUtility()


def _load_service(monkeypatch):
    fake_razorpay = types.SimpleNamespace(Client=_FakeClient)
    monkeypatch.setitem(sys.modules, "razorpay", fake_razorpay)
    sys.modules.pop("services.razorpay_service", None)
    return importlib.import_module("services.razorpay_service")


def test_verify_webhook_signature_uses_raw_body(monkeypatch):
    service = _load_service(monkeypatch)
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_123")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "whsec")

    service.verify_webhook_signature(body=b'{"ok": true}', signature="sig")


def test_payment_captured_payload_normalizes_to_paid(monkeypatch):
    service = _load_service(monkeypatch)
    event = {
        "id": "evt_123",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_123",
                    "order_id": "order_123",
                    "status": "captured",
                    "notes": {"user_id": "user_1", "plan": "pro"},
                }
            }
        },
    }

    normalized = service.normalize_webhook_event(event)

    assert normalized["event_id"] == "evt_123"
    assert normalized["event_type"] == "payment.captured"
    assert normalized["order_id"] == "order_123"
    assert normalized["payment_id"] == "pay_123"
    assert normalized["payment_status"] == "paid"
    assert normalized["metadata"] == {"user_id": "user_1", "plan": "pro"}


def test_subscription_cancelled_payload_normalizes_to_cancelled(monkeypatch):
    service = _load_service(monkeypatch)
    event = {
        "id": "evt_456",
        "event": "subscription.cancelled",
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_123",
                    "status": "cancelled",
                    "notes": {"user_id": "user_1"},
                }
            }
        },
    }

    normalized = service.normalize_webhook_event(event)

    assert normalized["event_id"] == "evt_456"
    assert normalized["subscription_id"] == "sub_123"
    assert normalized["payment_status"] == "cancelled"
    assert normalized["metadata"] == {"user_id": "user_1"}
