import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import string

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_target = f"test_vault_{self.random_suffix}_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
                os.rmdir(os.path.dirname(self.storage_target))
            except Exception:
                pass

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new()

    def test_start_new_success(self):
        db_storage = MagicMock()
        expected_save_res = uuid.uuid4().hex
        db_storage.save.return_value = expected_save_res

        mock_extractor = MagicMock()
        mock_parser = MagicMock()
        mock_reporter = MagicMock()
        
        expected_payload = {"status": "".join(random.choices(string.ascii_lowercase, k=5)), "audit_id": uuid.uuid4().hex}
        mock_reporter.generate.return_value = expected_payload

        kwargs = {
            "db_storage": db_storage,
            f"extractor_tool_{uuid.uuid4().hex[:6]}": mock_extractor,
            "market_parser": mock_parser,
            "market_portfolio_stress_reporter": mock_reporter
        }

        result = start_new(**kwargs)

        mock_extractor.extract.assert_called_once()
        mock_parser.parse_stream.assert_called_once()
        mock_reporter.generate.assert_called_once()
        db_storage.save.assert_called_once_with(expected_payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], expected_save_res)
        self.assertEqual(result["payload"], expected_payload)

    def test_start_new_default_payload(self):
        db_storage = MagicMock()
        db_storage.save.return_value = uuid.uuid4().hex

        result = start_new(db_storage=db_storage)
        self.assertEqual(result["payload"], {"status": "ok"})
        db_storage.save.assert_called_once_with({"status": "ok"})

    def test_start_new_invalid_payload_type(self):
        db_storage = MagicMock()
        mock_reporter = MagicMock()
        invalid_payload = random.randint(1000, 9999)
        mock_reporter.generate.return_value = invalid_payload

        with self.assertRaises(TypeError):
            start_new(db_storage=db_storage, market_portfolio_stress_reporter=mock_reporter)

    def test_process_audit_data_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id,
            "metric": random.uniform(10.0, 100.0)
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, audit_data)

    def test_process_audit_data_invalid_type(self):
        invalid_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, invalid_data)

    def test_validate_storage_target_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {"audit_id": audit_id, "data": random.randint(1, 100)}
        
        market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)
        
        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, audit_id)
        self.assertTrue(is_valid)

    def test_validate_storage_target_invalid_id(self):
        audit_id = uuid.uuid4().hex
        wrong_id = uuid.uuid4().hex
        audit_data = {"audit_id": audit_id}
        
        market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)
        
        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_id)
        self.assertFalse(is_valid)

    def test_validate_storage_target_not_found(self):
        non_existent_target = f"ghost_{uuid.uuid4().hex}.json"
        is_valid = market_portfolio_stress_audit_summary_vault_validate(non_existent_target, uuid.uuid4().hex)
        self.assertFalse(is_valid)

    def test_validate_storage_target_corrupted_json(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write("{corrupted_json_data")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, uuid.uuid4().hex)
        self.assertFalse(is_valid)

    def test_export_storage_target_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {"audit_id": audit_id, "val": uuid.uuid4().hex}
        format_type = "".join(random.choices(string.ascii_lowercase, k=4))

        market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        export_res = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=format_type)

        self.assertEqual(export_res["format"], format_type)
        self.assertEqual(export_res["data"], audit_data)

    def test_export_storage_target_not_found(self):
        non_existent_target = f"ghost_{uuid.uuid4().hex}.json"
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(non_existent_target)

if __name__ == "__main__":
    unittest.main()