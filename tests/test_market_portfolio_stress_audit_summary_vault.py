import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import tempfile
import io

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.random_audit_id = uuid.uuid4().hex
        self.random_target = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.random_target):
            try:
                os.remove(self.random_target)
            except OSError:
                pass

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_start_new_success_flow(self):
        mock_db = MagicMock()
        random_save_res = uuid.uuid4().hex
        mock_db.save.return_value = random_save_res

        mock_extractor = MagicMock()
        mock_parser = MagicMock()
        mock_reporter = MagicMock()
        
        generated_payload = {
            "status": uuid.uuid4().hex,
            "audit_id": self.random_audit_id,
            "risk_score": random.randint(1, 100)
        }
        mock_reporter.generate.return_value = generated_payload

        kwargs = {
            "db_storage": mock_db,
            "extractor_tool_1790087207": mock_extractor,
            "market_parser": mock_parser,
            "market_portfolio_stress_reporter": mock_reporter
        }

        result = start_new(**kwargs)

        mock_extractor.extract.assert_called_once()
        mock_parser.parse_stream.assert_called_once()
        mock_reporter.generate.assert_called_once()
        mock_db.save.assert_called_once_with(generated_payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], random_save_res)
        self.assertEqual(result["payload"], generated_payload)

    def test_start_new_default_payload_when_none(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        mock_reporter.generate.return_value = None

        kwargs = {
            "db_storage": mock_db,
            "market_portfolio_stress_reporter": mock_reporter
        }

        result = start_new(**kwargs)
        self.assertEqual(result["payload"], {"status": "ok"})
        mock_db.save.assert_called_once_with({"status": "ok"})

    def test_start_new_invalid_payload_type(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        mock_reporter.generate.return_value = random.choice([random.randint(1, 500), "string_payload", [1, 2, 3]])

        kwargs = {
            "db_storage": mock_db,
            "market_portfolio_stress_reporter": mock_reporter
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_process_audit_data_invalid_type(self):
        invalid_data = random.choice([uuid.uuid4().hex, random.randint(100, 999), None, [1, 2, 3]])
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.random_target, invalid_data)

    def test_process_and_validate_audit_data(self):
        audit_data = {
            "audit_id": self.random_audit_id,
            "telemetry_metric": random.uniform(0.1, 99.9),
            "risk_flag": random.choice([True, False])
        }

        process_res = market_portfolio_stress_audit_summary_vault_process(self.random_target, audit_data)
        
        self.assertEqual(process_res["status"], "saved")
        self.assertEqual(process_res["audit_id"], self.random_audit_id)
        self.assertTrue(os.path.exists(self.random_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.random_target, self.random_audit_id)
        self.assertTrue(is_valid)

        wrong_audit_id = uuid.uuid4().hex
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(self.random_target, wrong_audit_id)
        self.assertFalse(is_invalid)

    def test_validate_nonexistent_target(self):
        nonexistent_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")
        result = market_portfolio_stress_audit_summary_vault_validate(nonexistent_path, self.random_audit_id)
        self.assertFalse(result)

    def test_validate_corrupted_json(self):
        with open(self.random_target, "w", encoding="utf-8") as f:
            f.write("corrupted_json_payload_" + uuid.uuid4().hex)

        result = market_portfolio_stress_audit_summary_vault_validate(self.random_target, self.random_audit_id)
        self.assertFalse(result)

    def test_export_storage_target_success(self):
        audit_data = {
            "audit_id": self.random_audit_id,
            "payload_data": uuid.uuid4().hex
        }
        market_portfolio_stress_audit_summary_vault_process(self.random_target, audit_data)

        format_type = random.choice(["json", "yaml", "xml"])
        export_res = market_portfolio_stress_audit_summary_vault_export(self.random_target, format=format_type)

        self.assertEqual(export_res["format"], format_type)
        self.assertEqual(export_res["data"], audit_data)

    def test_export_storage_target_not_found(self):
        nonexistent_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(nonexistent_path)

if __name__ == "__main__":
    unittest.main()