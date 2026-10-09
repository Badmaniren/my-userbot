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
    def __init__(self, target_path):
        self.target_path = target_path

    def save(self, payload):
        with open(self.target_path, "w", encoding="utf-8") as f:
            import json
            json.dump(payload, f)
        return {"path": self.target_path, "status": "saved_by_db"}

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
    def __init__(self, data):
        self.data = data

    def generate(self):
        return self.data

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.filename = f"audit_{uuid.uuid4()}.json"
        self.storage_target = os.path.join(self.test_dir.name, self.filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_integration_pipeline_and_vault_lifecycle(self):
        rand_audit_id = str(uuid.uuid4())
        rand_metric = random.uniform(10.0, 1000.0)
        payload_data = {
            "audit_id": rand_audit_id,
            "stress_metric": rand_metric,
            "status": "completed"
        }

        db_storage = RealDummyDbStorage(self.storage_target)
        extractor = RealDummyExtractor()
        parser = RealDummyParser()
        reporter = RealDummyReporter(payload_data)

        start_result = start_new(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor,
            market_parser=parser,
            market_portfolio_stress_reporter=reporter
        )

        self.assertEqual(start_result["status"], "success")
        self.assertEqual(start_result["payload"]["audit_id"], rand_audit_id)
        self.assertTrue(extractor.extracted)
        self.assertTrue(parser.parsed)
        self.assertTrue(os.path.exists(self.storage_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, rand_audit_id)
        self.assertTrue(is_valid)

        export_res = market_portfolio_stress_audit_summary_vault_export(self.storage_target, format="json")
        self.assertEqual(export_res["format"], "json")
        self.assertEqual(export_res["data"]["audit_id"], rand_audit_id)
        self.assertEqual(export_res["data"]["stress_metric"], rand_metric)

        new_filename = f"proc_{uuid.uuid4()}.json"
        new_target = os.path.join(self.test_dir.name, new_filename)
        audit_data = {
            "audit_id": rand_audit_id,
            "data": random.randint(1000, 9999)
        }

        proc_res = market_portfolio_stress_audit_summary_vault_process(new_target, audit_data)
        self.assertEqual(proc_res["status"], "saved")
        self.assertEqual(proc_res["audit_id"], rand_audit_id)
        self.assertTrue(os.path.exists(new_target))

        self.assertTrue(market_portfolio_stress_audit_summary_vault_validate(new_target, rand_audit_id))

    def test_validation_failure_on_corrupted_json(self):
        rand_audit_id = str(uuid.uuid4())
        with open(self.storage_target, "w", encoding="utf-8") as f:
            f.write("INVALID_CORRUPTED_JSON{{{")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.storage_target, rand_audit_id)
        self.assertFalse(is_valid)

if __name__ == "__main__":
    unittest.main()