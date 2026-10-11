import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_stress_audit_compliance_bridge import (
    ComplianceAuditException,
    MarketPortfolioStressAuditComplianceBridge,
    market_portfolio_stress_audit_compliance_bridge
)

class TestMarketPortfolioStressAuditComplianceBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.standard = uuid.uuid4().hex
        self.stream_id = uuid.uuid4().hex
        self.status = random.choice(["COMPLIANT", "NON_COMPLIANT", "PENDING", "WARNING"])

        self.mock_db = MagicMock()
        self.mock_compliance_hub = MagicMock()
        self.mock_exporter = MagicMock()

        self.bridge = MarketPortfolioStressAuditComplianceBridge(
            db_storage=self.mock_db,
            market_portfolio_audit_compliance_hub=self.mock_compliance_hub,
            market_portfolio_stress_audit_exporter_v2=self.mock_exporter
        )

    def test_audit_and_validate_success(self):
        expected_audit_data = {
            "portfolio_id": self.portfolio_id,
            "standard": self.standard,
            "status": self.status,
            "nonce": random.randint(1000, 9999)
        }
        self.mock_compliance_hub.verify_compliance.return_value = expected_audit_data

        result = self.bridge.audit_and_validate(self.portfolio_id, self.standard)

        self.mock_compliance_hub.verify_compliance.assert_called_once_with(self.portfolio_id, self.standard)
        self.mock_db.log_audit_event.assert_called_once_with(expected_audit_data)
        self.assertEqual(result, expected_audit_data)

    def test_audit_and_validate_no_db(self):
        bridge_no_db = MarketPortfolioStressAuditComplianceBridge(
            market_portfolio_audit_compliance_hub=self.mock_compliance_hub
        )
        expected_audit_data = {
            "portfolio_id": self.portfolio_id,
            "status": self.status
        }
        self.mock_compliance_hub.verify_compliance.return_value = expected_audit_data

        result = bridge_no_db.audit_and_validate(self.portfolio_id, self.standard)

        self.mock_compliance_hub.verify_compliance.assert_called_once_with(self.portfolio_id, self.standard)
        self.assertEqual(result, expected_audit_data)

    def test_export_audit_stream(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)
        self.mock_exporter.export_stream.return_value = mock_stream

        result_stream = self.bridge.export_audit_stream(self.stream_id)

        self.mock_exporter.export_stream.assert_called_once_with(self.stream_id)
        self.assertEqual(result_stream.read(), random_bytes)

    def test_process_stress_event(self):
        payload = {
            "event_id": uuid.uuid4().hex,
            "severity": random.uniform(1.0, 10.0),
            "metric": uuid.uuid4().hex
        }
        expected_save_result = {"status": "saved", "id": payload["event_id"]}
        self.mock_db.save_event.return_value = expected_save_result

        result = self.bridge.process_stress_event(payload)

        self.mock_db.save_event.assert_called_once_with(payload)
        self.assertEqual(result, expected_save_result)

    def test_wrapper_function(self):
        bridge_input = {
            "portfolio_id": self.portfolio_id,
            "compliance_report": {
                "status": self.status,
                "score": random.random()
            }
        }

        result = market_portfolio_stress_audit_compliance_bridge(bridge_input)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["audit_compliance_status"], self.status)
        self.assertTrue(result["bridge_processed"])

    def test_wrapper_function_default_status(self):
        bridge_input = {
            "portfolio_id": self.portfolio_id
        }

        result = market_portfolio_stress_audit_compliance_bridge(bridge_input)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["audit_compliance_status"], "COMPLIANT")
        self.assertTrue(result["bridge_processed"])


class TestMarketPortfolioStressAuditComplianceBridgeIntegration(unittest.TestCase):

    def test_integration_flow(self):
        portfolio_id = uuid.uuid4().hex
        standard = uuid.uuid4().hex
        status = random.choice(["PASSED", "FAILED", "REVIEW"])

        with patch("skills.market_portfolio_stress_audit_compliance_bridge.market_portfolio_audit_compliance_hub") as mock_hub_module, \
             patch("skills.market_portfolio_stress_audit_compliance_bridge.db_storage") as mock_db_module:

            mock_hub = MagicMock()
            mock_hub.verify_compliance.return_value = {"portfolio_id": portfolio_id, "status": status}

            bridge = MarketPortfolioStressAuditComplianceBridge(
                db_storage=mock_db_module,
                market_portfolio_audit_compliance_hub=mock_hub
            )

            audit_res = bridge.audit_and_validate(portfolio_id, standard)
            self.assertEqual(audit_res["status"], status)
            mock_db_module.log_audit_event.assert_called_once()

            wrapper_input = {
                "portfolio_id": portfolio_id,
                "compliance_report": audit_res
            }
            wrapped_res = market_portfolio_stress_audit_compliance_bridge(wrapper_input)
            self.assertEqual(wrapped_res["audit_compliance_status"], status)
            self.assertTrue(wrapped_res["bridge_processed"])