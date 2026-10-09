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
        self.storage_target = f"test_audit_storage_{self.random_suffix}.json"

    def tearDown(self):
        if os.path.exists(self.storage_target):
            try:
                os.remove(self.storage_target)
            except OSError:
                pass
        dirname = os.path.dirname(self.storage_target)
        if dirname and os.path.exists(dirname):
            try:
                os.rmdir(dirname)
            except OSError:
                pass

    def test_start_new_missing_db_storage(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_start_new_invalid_payload_type(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        invalid_payload = "".join(random.choices(string.ascii_letters, k=10))
        mock_reporter.generate.return_value = invalid_payload
        
        with self.assertRaises(TypeError):
            start_new(db_storage=mock_db, market_portfolio_stress_reporter=mock_reporter)

    def test_start_new_successful_execution(self):
        mock_db = MagicMock()
        expected_save_result = uuid.uuid4().hex
        mock_db.save.return_value = expected_save_result

        mock_extractor = MagicMock()
        mock_parser = MagicMock()
        mock_reporter = MagicMock()
        
        generated_payload = {
            "status": "ok",
            "metric": random.randint(100, 999),
            "identifier": uuid.uuid4().hex
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
        self.assertEqual(result["save_result"], expected_save_result)
        self.assertEqual(result["payload"], generated_payload)

    def test_start_new_default_payload_when_none(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        mock_reporter.generate.return_value = None

        result = start_new(db_storage=mock_db, market_portfolio_stress_reporter=mock_reporter)
        self.assertEqual(result["payload"], {"status": "ok"})
        mock_db.save.assert_called_once_with({"status": "ok"})

    def test_market_portfolio_stress_audit_summary_vault_process_invalid_data(self):
        invalid_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, invalid_data)

    def test_market_portfolio_stress_audit_summary_vault_process_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id,
            "score": random.random(),
            "timestamp": uuid.uuid4().hex
        }

        result = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, audit_data)

    def test_market_portfolio_stress_audit_summary_vault_validate_nonexistent(self):
        nonexistent_target = f"nonexistent_{uuid.uuid4().hex}.json"
        expected_id = uuid.uuid4().hex
        is_valid = market_portfolio_stress_audit_summary_vault_validate(nonexistent_target, expected_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_corrupted_json(self):
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write("corrupted_json_data_" + uuid.uuid4().hex)

        expected_id = uuid.uuid4().hex
        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, expected_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {"audit_id": audit_id}
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, audit_id)
        self.assertTrue(is_valid)

        wrong_id = uuid.uuid4().hex
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_id)
        self.assertFalse(is_invalid)

    def test_market_portfolio_stress_audit_summary_vault_export_nonexistent(self):
        nonexistent_target = f"nonexistent_export_{uuid.uuid4().hex}.json"
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(nonexistent_target)

    def test_market_portfolio_stress_audit_summary_vault_export_success(self):
        audit_data = {
            "audit_id": uuid.uuid4().hex,
            "data": random.randint(1, 100000)
        }
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        export_format = random.choice(["json", "csv", "xml"])
        exported = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=export_format)

        self.assertEqual(exported["format"], export_format)
        self.assertEqual(exported["data"], audit_data)