import os
import json
import uuid
import random
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import shutil

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)


class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.storage_target = os.path.join(self.test_dir, self.random_filename)
        self.audit_id = uuid.uuid4().hex
        self.random_payload_key = uuid.uuid4().hex
        self.random_payload_val = uuid.uuid4().hex

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_start_new_missing_db_storage(self):
        kwargs = {
            uuid.uuid4().hex: MagicMock()
        }
        with self.assertRaises(ValueError):
            start_new(**kwargs)

    def test_start_new_success_flow(self):
        mock_db_storage = MagicMock()
        expected_save_result = uuid.uuid4().hex
        mock_db_storage.save.return_value = expected_save_result

        mock_extractor = MagicMock()
        mock_parser = MagicMock()
        mock_reporter = MagicMock()
        
        generated_payload = {
            "status": uuid.uuid4().hex,
            self.random_payload_key: self.random_payload_val,
            "audit_id": self.audit_id
        }
        mock_reporter.generate.return_value = generated_payload

        kwargs = {
            "db_storage": mock_db_storage,
            uuid.uuid4().hex: mock_extractor,
            "market_parser": mock_parser,
            "market_portfolio_stress_reporter": mock_reporter
        }

        result = start_new(**kwargs)

        mock_extractor.extract.assert_called_once()
        mock_parser.parse_stream.assert_called_once()
        mock_reporter.generate.assert_called_once()
        mock_db_storage.save.assert_called_once_with(generated_payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], expected_save_result)
        self.assertEqual(result["payload"], generated_payload)

    def test_start_new_payload_none_fallback(self):
        mock_db_storage = MagicMock()
        mock_reporter = MagicMock()
        mock_reporter.generate.return_value = None

        kwargs = {
            "db_storage": mock_db_storage,
            "market_portfolio_stress_reporter": mock_reporter
        }

        result = start_new(**kwargs)
        mock_db_storage.save.assert_called_once_with({"status": "ok"})
        self.assertEqual(result["payload"], {"status": "ok"})

    def test_start_new_payload_invalid_type(self):
        mock_db_storage = MagicMock()
        mock_reporter = MagicMock()
        mock_reporter.generate.return_value = random.randint(1000, 9999)

        kwargs = {
            "db_storage": mock_db_storage,
            "market_portfolio_stress_reporter": mock_reporter
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_process_audit_data_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, audit_data)

    def test_process_audit_data_invalid_type(self):
        invalid_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, invalid_data)

    def test_validate_storage_target_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertTrue(is_valid)

    def test_validate_storage_target_not_found(self):
        non_existent = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        is_valid = market_portfolio_stress_audit_summary_vault_validate(non_existent, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_corrupted_json(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write("{invalid_json: " + uuid.uuid4().hex)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_wrong_id(self):
        audit_data = {
            "audit_id": uuid.uuid4().hex
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertFalse(is_valid)

    def test_export_storage_target_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        format_type = uuid.uuid4().hex
        result = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=format_type)

        self.assertEqual(result["format"], format_type)
        self.assertEqual(result["data"], audit_data)

    def test_export_storage_target_not_found(self):
        non_existent = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(non_existent)


if __name__ == "__main__":
    unittest.main()