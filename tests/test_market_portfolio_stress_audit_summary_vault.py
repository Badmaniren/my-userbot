import unittest
import os
import json
import uuid
import random
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class TestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_start_new_execution_flow(self):
        mock_db = MagicMock()
        random_save_res = uuid.uuid4().hex
        mock_db.save.return_value = random_save_res
        
        mock_extractor = MagicMock()
        mock_reporter = MagicMock()
        random_payload = {"data": uuid.uuid4().hex}
        mock_reporter.generate.return_value = random_payload
        
        kwargs = {
            "db_storage": mock_db,
            "extractor_tool": mock_extractor,
            "market_portfolio_stress_reporter": mock_reporter
        }
        
        result = start_new(**kwargs)
        
        self.assertEqual(result["save_result"], random_save_res)
        self.assertEqual(result["payload"], random_payload)
        mock_extractor.extract.assert_called_once()
        mock_db.save.assert_called_with(random_payload)

    def test_process_and_validate_integrity(self):
        random_filename = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        random_audit_id = uuid.uuid4().hex
        audit_data = {"audit_id": random_audit_id, "val": random.random()}
        
        process_res = market_portfolio_stress_audit_summary_vault_process(random_filename, audit_data)
        
        self.assertEqual(process_res["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(random_filename))
        
        is_valid = market_portfolio_stress_audit_summary_vault_validate(random_filename, random_audit_id)
        self.assertTrue(is_valid)
        
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(random_filename, uuid.uuid4().hex)
        self.assertFalse(is_invalid)

    def test_export_functionality(self):
        random_filename = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        random_data = {"metrics": [random.random() for _ in range(5)], "id": uuid.uuid4().hex}
        
        with open(random_filename, "w") as f:
            json.dump(random_data, f)
            
        export_res = market_portfolio_stress_audit_summary_vault_export(random_filename, format="json")
        
        self.assertEqual(export_res["data"], random_data)
        self.assertEqual(export_res["format"], "json")

    def test_start_new_missing_db_raises(self):
        with self.assertRaises(ValueError):
            start_new(db_storage=None)

    def test_process_invalid_data_type(self):
        random_filename = os.path.join(self.test_dir, f"{uuid.uuid4().hex}.json")
        with self.assertRaises(TypeError):
            market_portfolio_stress_audit_summary_vault_process(random_filename, "not_a_dict")

    def test_export_nonexistent_file(self):
        random_path = os.path.join(self.test_dir, uuid.uuid4().hex)
        with self.assertRaises(FileNotFoundError):
            market_portfolio_stress_audit_summary_vault_export(random_path)

if __name__ == "__main__":
    unittest.main()