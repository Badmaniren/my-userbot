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
        self.audit_id = uuid.uuid4().hex
        self.random_value = random.randint(1000, 99999)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new()

    def test_start_new_invalid_payload_type(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        rand_string = uuid.uuid4().hex
        stress_reporter_mock.generate.return_value = rand_string
        
        with self.assertRaises(TypeError):
            start_new(db_storage=db_storage_mock, market_portfolio_stress_reporter=stress_reporter_mock)

    def test_start_new_success_flow(self):
        db_storage_mock = MagicMock()
        save_return_val = uuid.uuid4().hex
        db_storage_mock.save.return_value = save_return_val

        extractor_mock = MagicMock()
        market_parser_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        
        expected_payload = {
            "status": uuid.uuid4().hex,
            "metric": self.random_value
        }
        stress_reporter_mock.generate.return_value = expected_payload

        kwargs = {
            "db_storage": db_storage_mock,
            f"extractor_tool_{uuid.uuid4().hex[:8]}": extractor_mock,
            "market_parser": market_parser_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        result = start_new(**kwargs)

        extractor_mock.extract.assert_called_once()
        market_parser_mock.parse_stream.assert_called_once()
        stress_reporter_mock.generate.assert_called_once()
        db_storage_mock.save.assert_called_once_with(expected_payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_return_val)
        self.assertEqual(result["payload"], expected_payload)

    def test_start_new_default_payload(self):
        db_storage_mock = MagicMock()
        result = start_new(db_storage=db_storage_mock)
        
        db_storage_mock.save.assert_called_once_with({"status": "ok"})
        self.assertEqual(result["payload"], {"status": "ok"})

    def test_process_audit_data_invalid_type(self):
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, uuid.uuid4().hex)

    def test_process_audit_data_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            "data": uuid.uuid4().hex,
            "val": self.random_value
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data["audit_id"], self.audit_id)
        self.assertEqual(loaded_data["val"], self.random_value)

    def test_validate_storage_target_not_found(self):
        non_existent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        is_valid = market_portfolio_stress_audit_summary_vault_validate(non_existent_path, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_corrupted_json(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "{invalid_json")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_success_and_mismatch(self):
        audit_data = {
            "audit_id": self.audit_id,
            "random_field": uuid.uuid4().hex
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        # Mismatch test
        wrong_id = uuid.uuid4().hex
        self.assertFalse(market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_id))

        # Success test
        self.assertTrue(market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id))

    def test_export_storage_target_not_found(self):
        non_existent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(non_existent_path)

    def test_export_storage_target_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            "payload_data": uuid.uuid4().hex,
            "score": self.random_value
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        format_name = uuid.uuid4().hex[:6]
        export_result = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=format_name)

        self.assertEqual(export_result["format"], format_name)
        self.assertEqual(export_result["data"], audit_data)


if __name__ == "__main__":
    unittest.main()