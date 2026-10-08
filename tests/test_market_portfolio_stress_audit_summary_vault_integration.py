import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealDummyDbStorage:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def save(self, payload):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return {"saved_to": self.storage_path, "bytes": len(str(payload))}

class RealDummyExtractor:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True

class RealDummyParser:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True

class RealDummyReporter:
    def __init__(self, payload):
        self.payload = payload

    def generate(self):
        return self.payload

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.temp_dir.name, f"db_{uuid.uuid4().hex}.json")
        self.target_file = os.path.join(self.temp_dir.name, "sub", f"audit_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_full_workflow_and_validation(self):
        random_audit_id = f"audit-id-{uuid.uuid4().hex}"
        random_metric_value = random.uniform(100.0, 999.9)
        
        payload = {
            "audit_id": random_audit_id,
            "metric": random_metric_value,
            "status": "stress_tested"
        }

        db_storage = RealDummyDbStorage(self.db_file)
        extractor = RealDummyExtractor()
        parser = RealDummyParser()
        reporter = RealDummyReporter(payload)

        start_result = start_new(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor,
            market_parser=parser,
            market_portfolio_stress_reporter=reporter
        )

        self.assertEqual(start_result["status"], "success")
        self.assertEqual(start_result["payload"]["audit_id"], random_audit_id)
        self.assertTrue(extractor.extracted)
        self.assertTrue(parser.parsed)
        self.assertTrue(os.path.exists(self.db_file))

        process_result = market_portfolio_stress_audit_summary_vault_process(
            storage_target=self.target_file,
            audit_data=payload
        )

        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(self.target_file))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=self.target_file,
            expected_audit_id=random_audit_id
        )
        self.assertTrue(is_valid)

        invalid_check = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=self.target_file,
            expected_audit_id="wrong-audit-id"
        )
        self.assertFalse(invalid_check)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            storage_target=self.target_file,
            format="json"
        )
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], random_audit_id)
        self.assertEqual(export_result["data"]["metric"], random_metric_value)

if __name__ == "__main__":
    unittest.main()