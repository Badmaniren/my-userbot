import logging
import hmac
import hashlib
import json
import requests

logger = logging.getLogger(__name__)


class WebhookPayloadValidationError(Exception):
    """Вызывается, когда полезная нагрузка вебхука не проходит валидацию."""
    pass


class WebhookDispatchError(Exception):
    """Вызывается при сбое отправки вебхука (сетевые ошибки, неверный HTTP статус)."""
    pass


class StressAuditWebhookDispatcher:
    def __init__(self, webhook_url: str, secret_token: str):
        self.webhook_url = webhook_url
        self.secret_token = secret_token

    def _validate_payload(self, payload: dict) -> None:
        required_fields = ["audit_id", "portfolio_id", "status"]
        for field in required_fields:
            if field not in payload:
                raise WebhookPayloadValidationError(f"Missing required field: {field}")

        if "var_value" not in payload and "stress_loss_amount" not in payload:
            raise WebhookPayloadValidationError("Missing required field: var_value")

        var_val = payload.get("var_value", payload.get("stress_loss_amount"))
        if not isinstance(var_val, (int, float)):
            raise WebhookPayloadValidationError("Field 'var_value' must be numeric")

    def _generate_signature(self, payload_bytes: bytes) -> str:
        return hmac.new(
            self.secret_token.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

    def dispatch(self, payload: dict) -> bool:
        self._validate_payload(payload)

        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = self._generate_signature(payload_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature
        }

        try:
            response = requests.post(self.webhook_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.error(f"Network error during webhook dispatch: {e}")
            raise WebhookDispatchError(f"Network error: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during webhook dispatch: {e}")
            raise WebhookDispatchError(f"HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception during webhook dispatch: {e}")
            raise WebhookDispatchError(f"Request exception: {e}")

        return True


def market_portfolio_stress_audit_webhook_dispatcher(audit_id: str, webhook_url: str, payload: dict) -> dict:
    from skills.db_storage import db_storage

    dispatcher = StressAuditWebhookDispatcher(webhook_url=webhook_url, secret_token="integration_secret")

    validation_payload = payload.copy()
    if "var_value" not in validation_payload and "stress_loss_amount" in validation_payload:
        validation_payload["var_value"] = abs(validation_payload["stress_loss_amount"])

    dispatcher.dispatch(validation_payload)

    db_storage(
        operation="update",
        table="stress_audit_webhooks",
        filters={"audit_id": audit_id},
        data={"status": "DISPATCHED"}
    )

    return {
        "dispatch_id": audit_id,
        "status": "SUCCESS",
        "audit_id": audit_id
    }