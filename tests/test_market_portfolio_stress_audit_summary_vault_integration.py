import unittest
import os
import json
import uuid
import tempfile
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealDatabaseStorageStub:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def save(self, payload):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return {"saved_to": self.storage_path, "status": "persisted"}

class RealExtractorToolStub:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True

class RealMarketParserStub:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True

class RealStressReporterStub:
    def __init__(self, dynamic_id, dynamic_value):
        self.dynamic_id = dynamic_id
        self.dynamic_value = dynamic_value

    def generate(self):
        return {
            "audit_id": self.dynamic_id,
            "metric_value": self.dynamic_value,
            "status": "stress_tested"
        }

class IntegrationTestMarketPortfolioStressAuditSummaryVault(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.test_dir.name, f"db_{uuid.uuid4().hex}.json")
        self.target_file = os.path.join(self.test_dir.name, "subfolder", f"audit_target_{uuid.uuid4().hex}.json")
        
        self.db_storage = RealDatabaseStorageStub(self.db_file)
        self.extractor = RealExtractorToolStub()
        self.market_parser = RealMarketParserStub()
        
        self.random_audit_id = f"audit-{uuid.uuid4()}"
        self.random_metric = uuid.uuid4().int
        self.stress_reporter = RealStressReporterStub(self.random_audit_id, self.random_metric)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_integration_workflow(self):
        start_result = start_new(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor,
            market_parser=self.market_parser,
            market_portfolio_stress_reporter=self.stress_reporter
        )

        self.assertTrue(self.extractor.extracted)
        self.assertTrue(self.market_parser.parsed)
        self.assertEqual(start_result["status"], "success")
        self.assertEqual(start_result["payload"]["audit_id"], self.random_audit_id)
        self.assertEqual(start_result["payload"]["metric_value"], self.random_metric)
        
        self.assertTrue(os.path.exists(self.db_file))
        with open(self.db_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
        self.assertEqual(persisted_data["audit_id"], self.random_audit_id)

        audit_data_to_process = {
            "audit_id": self.random_audit_id,
            "data": "complex_stress_matrix_payload",
            "val": self.random_metric
        }
        
        process_result = market_portfolio_stress_audit_summary_vault_process(
            self.target_file, 
            audit_data_to_process
        )
        
        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], self.random_audit_id)
        self.assertTrue(os.path.exists(self.target_file))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            self.target_file, 
            self.random_audit_id
        )
        self.assertTrue(is_valid)

        invalid_check = market_portfolio_stress_audit_summary_vault_validate(
            self.target_file, 
            "wrong-audit-id"
        )
        self.assertFalse(invalid_check)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            self.target_file, 
            format="json"
        )
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], self.random_audit_id)
        self.assertEqual(export_result["data"]["val"], self.random_metric)

if __name__ == "__main__":
    unittest.main()