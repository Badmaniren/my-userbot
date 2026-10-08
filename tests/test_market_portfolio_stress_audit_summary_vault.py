import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
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
        self.audit_id = str(uuid.uuid4())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_start_new_success_execution(self):
        db_storage_mock = MagicMock()
        save_return_val = {"saved_id": uuid.uuid4().hex}
        db_storage_mock.save.return_value = save_return_val

        extractor_mock = MagicMock()
        market_parser_mock = MagicMock()
        stress_reporter_mock = MagicMock()

        generated_payload = {
            "status": uuid.uuid4().hex,
            "metric": random.randint(100, 999)
        }
        stress_reporter_mock.generate.return_value = generated_payload

        kwargs = {
            "db_storage": db_storage_mock,
            "extractor_tool_1790087207": extractor_mock,
            "market_parser": market_parser_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        result = start_new(**kwargs)

        extractor_mock.extract.assert_called_once()
        market_parser_mock.parse_stream.assert_called_once()
        stress_reporter_mock.generate.assert_called_once()
        db_storage_mock.save.assert_called_once_with(generated_payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_return_val)
        self.assertEqual(result["payload"], generated_payload)

    def test_start_new_payload_none_fallback(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        stress_reporter_mock.generate.return_value = None

        kwargs = {
            "db_storage": db_storage_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        result = start_new(**kwargs)
        default_payload = {"status": "ok"}
        db_storage_mock.save.assert_called_once_with(default_payload)
        self.assertEqual(result["payload"], default_payload)

    def test_start_new_invalid_payload_type(self):
        db_storage_mock = MagicMock()
        stress_reporter_mock = MagicMock()
        invalid_payload = uuid.uuid4().hex
        stress_reporter_mock.generate.return_value = invalid_payload

        kwargs = {
            "db_storage": db_storage_mock,
            "market_portfolio_stress_reporter": stress_reporter_mock
        }

        with self.assertRaises(TypeError):
            start_new(**kwargs)

    def test_process_audit_data_invalid_type(self):
        not_a_dict = random.randint(1, 100)
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, not_a_dict)

    def test_process_audit_data_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            "data_key": uuid.uuid4().hex
        }

        res = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)
        
        self.assertEqual(res["status"], "saved")
        self.assertEqual(res["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, audit_data)

    def test_validate_storage_target_not_found(self):
        non_existent_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        is_valid = market_portfolio_stress_audit_summary_vault_validate(non_existent_path, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_json_decode_error(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + " invalid json {")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_success_mismatch(self):
        audit_data = {"audit_id": str(uuid.uuid4())}
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_success_match(self):
        audit_data = {"audit_id": self.audit_id}
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, self.audit_id)
        self.assertTrue(is_valid)

    def test_export_storage_target_not_found(self):
        non_existent_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(non_existent_path)

    def test_export_storage_target_success(self):
        audit_data = {
            "audit_id": self.audit_id,
            "metric": random.uniform(1.0, 100.0)
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        export_format = uuid.uuid4().hex
        res = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=export_format)

        self.assertEqual(res["format"], export_format)
        self.assertEqual(res["data"], audit_data)

if __name__ == "__main__":
    unittest.main()