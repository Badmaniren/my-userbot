import sys

try:
    import requests
except ImportError:
    class DummyRequestException(Exception):
        pass

    class DummyExceptionsModule:
        RequestException = DummyRequestException

    class DummyRequestsModule:
        exceptions = DummyExceptionsModule()
        RequestException = DummyRequestException

        @staticmethod
        def get(*args, **kwargs):
            raise DummyRequestException("requests library is not installed")

        @staticmethod
        def post(*args, **kwargs):
            raise DummyRequestException("requests library is not installed")

    requests = DummyRequestsModule()
    sys.modules['requests'] = requests

try:
    import skills.db_storage as _db_storage_mod
    db_storage = getattr(_db_storage_mod, "db_storage", None)
except Exception:
    db_storage = None

try:
    import skills.market_portfolio_stress_audit_summary_vault as _vault_mod
    market_portfolio_stress_audit_summary_vault = getattr(_vault_mod, "market_portfolio_stress_audit_summary_vault", None)
except Exception:
    market_portfolio_stress_audit_summary_vault = None


class MarketPortfolioStressAuditWebhookPublisher:
    def __init__(self, webhook_url: str, auth_token: str = None):
        self.webhook_url = webhook_url
        self.auth_token = auth_token

    def _get_headers(self):
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def publish(self, audit_payload: dict):
        headers = self._get_headers()
        response = requests.post(self.webhook_url, json=audit_payload, headers=headers)

        if response.status_code >= 400:
            error_id = audit_payload.get("error_tracking_id", "unknown")
            raise ValueError(f"Internal Server Error for {error_id}")

        return response.json()

    def publish_stream(self, report_meta: dict, file_stream):
        headers = self._get_headers()
        files = {"file": file_stream}
        data = report_meta

        response = requests.post(self.webhook_url, data=data, files=files, headers=headers)

        if response.status_code >= 400:
            raise ValueError(f"Stream publish failed with status code {response.status_code}")

        return response.json()


def _get_db_storage():
    mod = sys.modules.get("skills.db_storage")
    if mod and hasattr(mod, "db_storage"):
        return getattr(mod, "db_storage")
    try:
        from skills.db_storage import db_storage as ds
        return ds
    except Exception:
        return db_storage


def market_portfolio_stress_audit_webhook_publisher(audit_id: str, webhook_url: str):
    ds = _get_db_storage()
    stored_record = ds.get_audit_record(audit_id) if ds and hasattr(ds, "get_audit_record") else None
    payload = stored_record.get("data", {}) if stored_record else {"audit_id": audit_id}

    publisher = MarketPortfolioStressAuditWebhookPublisher(webhook_url=webhook_url)

    response = publisher.publish(payload)

    stored_record = ds.get_audit_record(audit_id) if ds and hasattr(ds, "get_audit_record") else None
    if stored_record:
        stored_record["webhook_dispatched"] = True
        if ds and hasattr(ds, "save_audit_record"):
            ds.save_audit_record(stored_record)

    return {
        "status": "success",
        "audit_id": audit_id,
        "delivery_status": "SUCCESS",
        "response": response
    }
