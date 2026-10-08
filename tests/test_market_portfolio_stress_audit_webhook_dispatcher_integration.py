import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_portfolio_stress_audit_webhook_dispatcher import market_portfolio_stress_audit_webhook_dispatcher
from skills.db_storage import db_storage


class TestMarketPortfolioStressAuditWebhookDispatcherIntegration(unittest.TestCase):

    @patch("requests.post")
    def test_webhook_dispatcher_integration(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        audit_id = f"audit_{uuid.uuid4()}"
        portfolio_id = f"port_{uuid.uuid4()}"
        var_value = round(random.uniform(1000.0, 50000.0), 2)

        webhook_url = "http://httpbin.org/post"

        payload = {
            "audit_id": audit_id,
            "portfolio_id": portfolio_id,
            "status": "COMPLETED",
            "var_value": var_value
        }

        db_storage(
            operation="insert",
            table="stress_audit_webhooks",
            data={
                "audit_id": audit_id,
                "portfolio_id": portfolio_id,
                "status": "PENDING"
            }
        )

        result = market_portfolio_stress_audit_webhook_dispatcher(
            audit_id=audit_id,
            webhook_url=webhook_url,
            payload=payload
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("audit_id"), audit_id)
        self.assertEqual(result.get("status"), "SUCCESS")

        stored_records = db_storage(
            operation="select",
            table="stress_audit_webhooks",
            filters={"audit_id": audit_id}
        )

        self.assertTrue(len(stored_records) > 0)
        updated_record = stored_records[0]
        self.assertEqual(updated_record.get("status"), "DISPATCHED")


if __name__ == "__main__":
    unittest.main()