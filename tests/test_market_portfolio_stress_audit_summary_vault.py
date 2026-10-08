import unittest
from unittest.mock import MagicMock, patch
import os
import json
import uuid
import random
import io
from skills import market_portfolio_stress_audit_summary_vault as vault

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.storage_target = f"test_vault_{self.random_prefix}.json"

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
            vault.start_new()

    def test_start_new_invalid_payload_type(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        rand_val = random.randint(1000, 9999)
        mock_reporter.generate.return_value = rand_val

        with self.assertRaises(TypeError):
            vault.start_new(db_storage=mock_db, market_portfolio_stress_reporter=mock_reporter)

    def test_start_new_success_flow(self):
        mock_db = MagicMock()
        save_return_val = uuid.uuid4().hex
        mock_db.save.return_value = save_return_val

        mock_extractor = MagicMock()
        mock_parser = MagicMock()
        mock_reporter = MagicMock()

        expected_key = uuid.uuid4().hex
        expected_val = uuid.uuid4().hex
        mock_reporter.generate.return_value = {expected_key: expected_val}

        kwargs = {
            "db_storage": mock_db,
            "extractor_tool": mock_extractor,
            "market_parser": mock_parser,
            "market_portfolio_stress_reporter": mock_reporter
        }

        result = vault.start_new(**kwargs)

        mock_extractor.extract.assert_called_once()
        mock_parser.parse_stream.assert_called_once()
        mock_reporter.generate.assert_called_once()
        mock_db.save.assert_called_once_with({expected_key: expected_val})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], save_return_val)
        self.assertEqual(result["payload"], {expected_key: expected_val})

    def test_market_portfolio_stress_audit_summary_vault_process_type_error(self):
        invalid_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            vault.market_portfolio_stress_audit_summary_vault_process(self.storage_target, invalid_data)

    def test_market_portfolio_stress_audit_summary_vault_process_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id,
            "scenario": uuid.uuid4().hex,
            "metrics": random.random()
        }

        result = vault.market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["audit_id"], audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, audit_data)

    def test_market_portfolio_stress_audit_summary_vault_validate_nonexistent(self):
        nonexistent_path = f"missing_{uuid.uuid4().hex}.json"
        expected_id = uuid.uuid4().hex
        is_valid = vault.market_portfolio_stress_audit_summary_vault_validate(nonexistent_path, expected_id)
        self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_corrupted_json(self):
        expected_id = uuid.uuid4().hex
        garbage_content = uuid.uuid4().bytes

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = io.BytesIO(garbage_content)
            is_valid = vault.market_portfolio_stress_audit_summary_vault_validate(self.storage_target, expected_id)
            self.assertFalse(is_valid)

    def test_market_portfolio_stress_audit_summary_vault_validate_mismatch_and_match(self):
        correct_id = uuid.uuid4().hex
        wrong_id = uuid.uuid4().hex
        audit_data = {"audit_id": correct_id}

        vault.market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        self.assertFalse(vault.market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_id))
        self.assertTrue(vault.market_portfolio_stress_audit_summary_vault_validate(self.storage_target, correct_id))

    def test_market_portfolio_stress_audit_summary_vault_export_file_not_found(self):
        nonexistent_path = f"missing_export_{uuid.uuid4().hex}.json"
        with self.assertRaises(FileNotFoundError):
            vault.market_portfolio_stress_audit_summary_vault_export(nonexistent_path)

    def test_market_portfolio_stress_audit_summary_vault_export_success(self):
        audit_id = uuid.uuid4().hex
        audit_data = {
            "audit_id": audit_id,
            "data_payload": uuid.uuid4().hex
        }
        vault.market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)

        export_format = uuid.uuid4().hex[:5]
        export_result = vault.market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=export_format)

        self.assertEqual(export_result["format"], export_format)
        self.assertEqual(export_result["data"], audit_data)

if __name__ == "__main__":
    unittest.main()