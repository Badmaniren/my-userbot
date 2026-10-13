import unittest
import unittest.mock
import os
import json
import uuid
import random
import tempfile
import shutil
from unittest.mock import MagicMock, patch
import skills.market_portfolio_stress_audit_summary_vault as vault

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_start_new_success_flow(self):
        mock_db = MagicMock()
        mock_db.save.return_value = random.randint(1000, 9999)
        
        mock_reporter = MagicMock()
        random_payload = {"audit_id": uuid.uuid4().hex, "val": random.random()}
        mock_reporter.generate.return_value = random_payload

        mock_parser = MagicMock()
        
        mock_extractor = MagicMock()

        result = vault.start_new(
            db_storage=mock_db,
            market_portfolio_stress_reporter=mock_reporter,
            market_parser=mock_parser,
            extractor_tool=mock_extractor
        )

        self.assertEqual(result["save_result"], mock_db.save.return_value)
        self.assertEqual(result["payload"], random_payload)
        mock_db.save.assert_called_once_with(random_payload)
        mock_extractor.extract.assert_called_once()
        mock_parser.parse_stream.assert_called_once()

    def test_start_new_missing_db_raises_value_error(self):
        with self.assertRaises(ValueError):
            vault.start_new(some_random_key=uuid.uuid4().hex)

    def test_process_and_validate_cycle(self):
        file_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        audit_id = uuid.uuid4().hex
        audit_data = {"audit_id": audit_id, "metrics": [random.random() for _ in range(5)]}

        process_res = vault.market_portfolio_stress_audit_summary_vault_process(file_path, audit_data)
        
        self.assertEqual(process_res["audit_id"], audit_id)
        self.assertTrue(os.path.exists(file_path))

        is_valid = vault.market_portfolio_stress_audit_summary_vault_validate(file_path, audit_id)
        self.assertTrue(is_valid)

        wrong_id = uuid.uuid4().hex
        is_invalid = vault.market_portfolio_stress_audit_summary_vault_validate(file_path, wrong_id)
        self.assertFalse(is_invalid)

    def test_export_functionality(self):
        file_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        random_data = {"key": uuid.uuid4().hex, "score": random.randint(0, 100)}
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(random_data, f)

        exported = vault.market_portfolio_stress_audit_summary_vault_export(file_path)
        
        self.assertEqual(exported["data"], random_data)
        self.assertEqual(exported["format"], "json")

    def test_process_invalid_data_type(self):
        file_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(TypeError):
            vault.market_portfolio_stress_audit_summary_vault_process(file_path, "not_a_dict")

    def test_validate_corrupted_file(self):
        file_path = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("invalid json content" + uuid.uuid4().hex)
        
        is_valid = vault.market_portfolio_stress_audit_summary_vault_validate(file_path, uuid.uuid4().hex)
        self.assertFalse(is_valid)

    def test_start_new_default_payload(self):
        mock_db = MagicMock()
        mock_db.save.return_value = True
        
        result = vault.start_new(db_storage=mock_db)
        
        self.assertEqual(result["payload"], {"status": "ok"})
        mock_db.save.assert_called_with({"status": "ok"})

if __name__ == "__main__":
    unittest.main()