import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import random
import io
import datetime

from skills.market_portfolio_stress_audit_compliance_validator import (
    MarketPortfolioStressAuditComplianceValidator,
    market_portfolio_stress_audit_compliance_validator
)


class TestMarketPortfolioStressAuditComplianceValidator(unittest.TestCase):

    def setUp(self):
        self.validator = MarketPortfolioStressAuditComplianceValidator()
        self.audit_id = str(uuid.uuid4())
        self.risk_threshold = round(random.uniform(0.01, 0.5), 4)

    @patch("skills.market_portfolio_stress_audit_summary_vault.fetch_audit_summary")
    def test_validate_audit_compliance_success(self, mock_fetch):
        mock_fetch.return_value = {
            "max_drawdown": self.risk_threshold - 0.05,
            "regulatory_status": "COMPLIANT"
        }

        result = self.validator.validate_audit_compliance(self.audit_id, self.risk_threshold)

        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertTrue(result["is_compliant"])
        self.assertEqual(result["violations"], [])
        self.assertIn("compliance_timestamp", result)

    @patch("skills.market_portfolio_stress_audit_summary_vault.fetch_audit_summary")
    def test_validate_audit_compliance_drawdown_violation(self, mock_fetch):
        exceeded_drawdown = self.risk_threshold + 0.1
        mock_fetch.return_value = {
            "max_drawdown": exceeded_drawdown,
            "regulatory_status": "COMPLIANT"
        }

        result = self.validator.validate_audit_compliance(self.audit_id, self.risk_threshold)

        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertFalse(result["is_compliant"])
        self.assertEqual(len(result["violations"]), 1)
        self.assertEqual(result["violations"][0]["metric"], "max_drawdown")
        self.assertEqual(result["violations"][0]["value"], exceeded_drawdown)
        self.assertEqual(result["violations"][0]["threshold"], self.risk_threshold)

    @patch("skills.market_portfolio_stress_audit_summary_vault.fetch_audit_summary")
    def test_validate_audit_compliance_status_violation(self, mock_fetch):
        mock_fetch.return_value = {
            "max_drawdown": self.risk_threshold - 0.05,
            "regulatory_status": "NON_COMPLIANT"
        }

        result = self.validator.validate_audit_compliance(self.audit_id, self.risk_threshold)

        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertFalse(result["is_compliant"])

    @patch("skills.market_portfolio_realtime_stream_ingestor.get_stream_reader")
    def test_process_stream_compliance(self, mock_get_stream_reader):
        stream_token = str(uuid.uuid4())
        stream_id_val = str(uuid.uuid4())

        mock_reader = MagicMock()
        mock_reader.read.return_value = json.dumps({"stream_id": stream_id_val}).encode("utf-8")
        mock_get_stream_reader.return_value = mock_reader

        result = self.validator.process_stream_compliance(stream_token)

        self.assertTrue(result["processed"])
        self.assertEqual(result["stream_id"], stream_id_val)

    def test_evaluate_single_rule_violation(self):
        metric_name = str(uuid.uuid4())
        max_lim = round(random.uniform(10.0, 100.0), 2)
        actual_val = max_lim + 10.0

        audit_payload = {metric_name: actual_val}
        rule_definition = {"metric": metric_name, "max_limit": max_lim}

        res = self.validator._evaluate_single_rule(audit_payload, rule_definition)

        self.assertIsNotNone(res)
        self.assertEqual(res["metric"], metric_name)
        self.assertEqual(res["value"], actual_val)
        self.assertEqual(res["max_limit"], max_lim)

    def test_evaluate_single_rule_no_violation(self):
        metric_name = str(uuid.uuid4())
        max_lim = round(random.uniform(10.0, 100.0), 2)
        actual_val = max_lim - 5.0

        audit_payload = {metric_name: actual_val}
        rule_definition = {"metric": metric_name, "max_limit": max_lim}

        res = self.validator._evaluate_single_rule(audit_payload, rule_definition)

        self.assertIsNone(res)

    @patch("skills.market_portfolio_audit_log_exporter.push_audit_log")
    def test_export_compliance_report(self, mock_push):
        export_target_str = str(uuid.uuid4())
        audit_res = {"audit_id": self.audit_id, "is_compliant": True}
        mock_push.return_value = {"status": "SUCCESS", "target": export_target_str}

        response = self.validator.export_compliance_report(audit_res, export_target_str)

        self.assertEqual(response["status"], "SUCCESS")
        self.assertEqual(response["target"], export_target_str)
        mock_push.assert_called_once_with(audit_res, export_target_str)


class TestMarketPortfolioStressAuditComplianceValidatorIntegration(unittest.TestCase):

    @patch("skills.market_portfolio_stress_audit_compliance_validator.db_storage")
    @patch("skills.market_portfolio_stress_audit_summary_vault.fetch_audit_summary")
    def test_compliance_validator_func_with_db_storage(self, mock_fetch, mock_db_storage):
        vault_key = str(uuid.uuid4())
        audit_id_val = str(uuid.uuid4())

        mock_db_storage.side_effect = [
            None,
            {"audit_id": audit_id_val, "compliance_score": 85.0}
        ]

        mock_fetch.return_value = {
            "audit_id": audit_id_val,
            "compliance_score": 85.0
        }

        result = market_portfolio_stress_audit_compliance_validator(vault_key)

        self.assertEqual(result["audit_id"], audit_id_val)
        self.assertTrue(result["is_compliant"])
        self.assertEqual(result["violations"], [])
        self.assertIn("compliance_timestamp", result)

    @patch("skills.market_portfolio_stress_audit_compliance_validator.db_storage")
    def test_compliance_validator_func_cached_in_db(self, mock_db_storage):
        vault_key = str(uuid.uuid4())
        audit_id_val = str(uuid.uuid4())

        mock_db_storage.return_value = {
            "audit_id": audit_id_val,
            "compliance_score": 25.0
        }

        result = market_portfolio_stress_audit_compliance_validator(vault_key)

        self.assertEqual(result["audit_id"], audit_id_val)
        self.assertFalse(result["is_compliant"])
        self.assertEqual(len(result["violations"]), 1)
        self.assertEqual(result["violations"][0]["metric"], "compliance_score")
        self.assertEqual(result["violations"][0]["value"], 25.0)
