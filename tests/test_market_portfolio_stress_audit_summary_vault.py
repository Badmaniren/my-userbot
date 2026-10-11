import os
import json
import uuid
import random
import unittest
from unittest.mock import MagicMock, patch
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    start_neos,
    market_portfolio_stress_audit_summary_vault_start,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.storage_target = f"{self_gen_path()}_{uuid.uuid4().hex[:6]}.json"

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

    def test_start_new_success_execution(self):
        mock_db = MagicMock()
        expected_save_res = f"saved_{uuid.uuid4().hex}"
        mock_db.save.return_value = expected_save_res

        mock_extractor = MagicMock()
        mock_parser = MagicMock()
        mock_reporter = MagicMock()
        
        gen_payload_key = f"key_{uuid.uuid4().hex[:4]}"
        gen_payload_val = f"val_{uuid.uuid4().hex[:4]}"
        mock_reporter.generate.return_value = {gen_payload_key: gen_payload_val}

        result = start_new(
            db_storage=mock_db,
            extractor_tool_1790087207=mock_extractor,
            market_parser=mock_parser,
            market_portfolio_stress_reporter=mock_reporter
        )

        mock_extractor.extract.assert_called_once()
        mock_parser.parse_stream.assert_called_once()
        mock_reporter.generate.assert_called_once()
        mock_db.save.assert_called_once_with({gen_payload_key: gen_payload_val})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], expected_save_res)
        self.assertEqual(result["payload"][gen_payload_key], gen_payload_val)

    def test_start_new_payload_none_fallback(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        mock_reporter.generate.return_value = None

        result = start_new(
            db_storage=mock_db,
            market_portfolio_stress_reporter=mock_reporter
        )

        self.assertEqual(result["payload"], {"status": "ok"})
        mock_db.save.assert_called_once_with({"status": "ok"})

    def test_start_new_payload_invalid_type(self):
        mock_db = MagicMock()
        mock_reporter = MagicMock()
        invalid_payload = random.randint(1000, 9999)
        mock_reporter.generate.return_value = invalid_payload

        with self.assertRaises(TypeError):
            start_new(
                db_storage=mock_db,
                market_portfolio_stress_reporter=mock_reporter
            )

    def test_aliases_pointing_to_start_new(self):
        self.assertEqual(start_neos, start_new)
        self.assertEqual(market_portfolio_stress_audit_summary_vault_start, start_new)

    def test_vault_process_saves_correctly(self):
        audit_id = f"aud_{uuid.uuid4().hex}"
        audit_data = {
            "audit_id": audit_id,
            "metric": random.random()
        }

        res = market_portfolio_stress_audit_summary_vault_process(self.storage_target, audit_data)
        
        self.assertEqual(res["status"], "saved")
        self.assertEqual(res["audit_id"], audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        with open(self.storage_target, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, audit_data)

    def test_vault_process_invalid_audit_data_type(self):
        invalid_data = f"str_instead_of_dict_{uuid.uuid4().hex}"
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(self.storage_target, invalid_data)

    def test_vault_validate_success(self):
        audit_id = f"aud_{uuid.uuid4().hex}"
        audit_data = {"audit_id": audit_id}
        
        dirname = os.path.dirname(self.storage_target)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, audit_id)
        self.assertTrue(is_valid)

    def test_vault_validate_file_not_found(self):
        fake_path = f"{uuid.uuid4().hex}.json"
        is_valid = market_portfolio_stress_audit_summary_vault_validate(fake_path, "any_id")
        self.assertFalse(is_valid)

    def test_vault_validate_corrupted_json(self):
        dirname = os.path.dirname(self.storage_target)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write("corrupted_json_content_" + uuid.uuid4().hex)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, "any_id")
        self.assertFalse(is_valid)

    def test_vault_validate_mismatched_id(self):
        audit_id = f"aud_{uuid.uuid4().hex}"
        wrong_id = f"aud_{uuid.uuid4().hex}"
        audit_data = {"audit_id": audit_id}
        
        dirname = os.path.dirname(self.storage_target)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, wrong_id)
        self.assertFalse(is_valid)

    def test_vault_export_success(self):
        audit_id = f"aud_{uuid.uuid4().hex}"
        audit_data = {"audit_id": audit_id, "data": random.randint(1, 100)}
        fmt = random.choice(["json", "csv", "xml"])

        dirname = os.path.dirname(self.storage_target)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        with open(self.storage_target, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        exported = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format=fmt)
        
        self.assertEqual(exported["format"], fmt)
        self.assertEqual(exported["data"], audit_data)

    def test_vault_export_file_not_found(self):
        fake_path = f"{uuid.uuid4().hex}.json"
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(fake_path)


def self_gen_path():
    return f"dir_{uuid.uuid4().hex[:6]}/vault_target_{uuid.uuid4().hex[:8]}"

if __name__ == '__main__':
    unittest.main()