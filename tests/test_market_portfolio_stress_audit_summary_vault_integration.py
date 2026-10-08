import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealDbStorage:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.saved_data = None

    def save(self, payload):
        self.saved_data = payload
        with open(self.storage_path, "w", encoding="utf-8") as f:
            import json
            json.dump(payload, f)
        return {"status": "persisted", "path": self.storage_path}

class RealExtractor:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True

class RealMarketParser:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True

class RealStressReporter:
    def __init__(self, payload):
        self.payload = payload

    def generate(self):
        return self.payload

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_file = os.path.join(self.test_dir.name, f"db_{uuid.uuid4().hex}.json")
        self.target_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.json")
        self.db_storage = RealDbStorage(self.db_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_start_new_integration_flow(self):
        rand_key = str(uuid.uuid4())
        rand_val = str(uuid.uuid4())
        payload_data = {"status": "audit_complete", "random_key": rand_key, "data": rand_val}

        extractor = RealExtractor()
        parser = RealMarketParser()
        reporter = RealStressReporter(payload_data)

        kwargs = {
            "db_storage": self.db_storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": parser,
            "market_portfolio_stress_reporter": reporter
        }

        result = start_new(**kwargs)

        self.assertTrue(extractor.extracted)
        self.assertTrue(parser.parsed)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], payload_data)
        self.assertEqual(self.db_storage.saved_data, payload_data)
        self.assertTrue(os.path.exists(self.db_file))

    def test_full_audit_lifecycle_integration(self):
        audit_id = str(uuid.uuid4())
        rand_metric = str(uuid.uuid4())
        audit_data = {
            "audit_id": audit_id,
            "metric": rand_metric,
            "details": "integration test execution"
        }

        process_res = market_portfolio_stress_audit_summary_vault_process(self.target_file, audit_data)
        self.assertEqual(process_res["status"], "saved")
        self.assertEqual(process_res["audit_id"], audit_id)
        self.assertTrue(os.path.exists(self.target_file))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.target_file, audit_id)
        self.assertTrue(is_valid)

        wrong_audit_id = str(uuid.uuid4())
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(self.target_file, wrong_audit_id)
        self.assertFalse(is_invalid)

        export_res = market_portfolio_stress_audit_summary_vault_export(self.target_file, format="json")
        self.assertEqual(export_res["format"], "json")
        self.assertEqual(export_res["data"], audit_data)

if __name__ == "__main__":
    unittest.main()