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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.storage_target = os.path.join(self.temp_dir.name, self.random_filename)
        self.expected_audit_id = uuid.uuid4().hex

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_start_new_success_execution(self):
        mock_db_storage = MagicMock()
        save_result_token = uuid.uuid4().hex
        mock_db_storage.save.return_value = save_result_token

        mock_extractor = MagicMock()
        mock_market_parser = MagicMock()
        mock_stress_reporter = MagicMock()
        generated_payload_key = uuid.uuid4().hex
        mock_stress_reporter.generate.return_value = {"status": generated_payload_key}

        kwargs = {
            "db_storage": mock_db_storage,
            "extractor_tool": mock_extractor,
            "market_parser": mock_market_parser,
            "market_portfolio_stress_reporter": mock_stress_reporter
        }

        result = start_new(**kwargs)

        mock_extractor.extract.assert_called_once()
        mock_market_parser.parse_stream.assert_called_once()
        mock_stress_reporter.generate.assert_called_once()
        mock_db_storage.save.assert_called_once_with({"status": generated_payload_key})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_result_token)
        self.assertEqual(result["payload"], {"status": generated_payload_key})

    def test_start_new_payload_type_error(self):
        mock_db_storage = MagicMock()
        mock_stress_reporter = MagicMock()
        invalid_payload = random.randint(1000, 9999)
        mock_stress_reporter.generate.return_value = invalid_payload

        kwargs = {
            "db_storage": mock_db_storage,
            "market_portfolio_stress_reporter": mock_stress_reporter
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_process_audit_data_success(self):
        audit_data = {
            "audit_id": self.expected_audit_id,
            "metric": random.uniform(1.0, 100.0)
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], self.expected_audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data["audit_id"], self.expected_audit_id)
        self.assertEqual(loaded_data["metric"], audit_data["metric"])

    def test_process_audit_data_type_error(self):
        invalid_audit_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, invalid_audit_data)

    def test_validate_storage_target_not_found(self):
        non_existent_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        is_valid = market_portfolio_stress_audit_summary_vault_validate(non_existent_target, self.expected_audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_corrupted_json(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + " invalid json data {{{")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.expected_audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_success(self):
        audit_data = {"audit_id": self.expected_audit_id}
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.expected_audit_id)
        self.assertTrue(is_valid)

        wrong_id = uuid.uuid4().hex
        is_valid_wrong = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_id)
        self.assertFalse(is_valid_wrong)

    def test_export_storage_target_not_found(self):
        non_existent_target = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(non_existent_target)

    def test_export_storage_target_success(self):
        audit_data = {
            "audit_id": self.expected_audit_id,
            "random_val": random.randint(10, 500)
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        export_format = uuid.uuid4().hex[:6]
        export_result = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=export_format)

        self.assertEqual(export_result["format"], export_format)
        self.assertEqual(export_result["data"]["audit_id"], self.expected_audit_id)
        self.assertEqual(export_result["data"]["random_val"], audit_data["random_val"])

    def test_stream_mock_io_behavior(self):
        mock_db_storage = MagicMock()
        mock_stress_reporter = MagicMock()
        
        random_payload_content = uuid.uuid4().hex
        mock_stress_reporter.generate.return_value = {"content": random_payload_content}

        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch("skills.market_portfolio_stress_audit_summary_vault.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = stream_data.read()
            
            result = start_new(db_storage=mock_db_storage, market_portfolio_stress_reporter=mock_stress_reporter)
            self.assertEqual(result["payload"]["content"], random_payload_content)
            mock_db_storage.save.assert_called_once()

if __name__ == "__main__":
    unittest.main()