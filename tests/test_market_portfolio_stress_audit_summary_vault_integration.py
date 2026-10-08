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

class RealDbStorage:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def save(self, payload):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            import json
            json.dump(payload, f)
        return {"saved_to": self.storage_path, "bytes": random.randint(100, 9999)}

class RealExtractorTool:
    def __init__(self, data_id):
        self.data_id = data_id
        self.extracted = False

    def extract(self):
        self.extracted = True
        return {"extracted_id": self.data_id}

class RealMarketParser:
    def __init__(self, parsed_value):
        self.parsed_value = parsed_value
        self.parsed = False

    def parse_stream(self):
        self.parsed = True
        return {"parsed_value": self.parsed_value}

class RealStressReporter:
    def __init__(self, report_data):
        self.report_data = report_data

    def generate(self):
        return self.report_data

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.json")
        self.db_storage = RealDbStorage(self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_start_new_integration_flow(self):
        random_audit_id = f"audit-id-{uuid.uuid4()}"
        random_score = random.uniform(10.0, 99.9)
        
        extractor = RealExtractorTool(uuid.uuid4().hex)
        parser = RealMarketParser(random.randint(1, 1000))
        
        expected_payload = {
            "status": "completed",
            "audit_id": random_audit_id,
            "stress_score": random_score
        }
        stress_reporter = RealStressReporter(expected_payload)

        kwargs = {
            "db_storage": self.db_storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": parser,
            "market_portfolio_stress_reporter": stress_reporter
        }

        result = start_new(**kwargs)

        self.assertTrue(extractor.extracted)
        self.assertTrue(parser.parsed)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], expected_payload)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_vault_process_validate_export_lifecycle(self):
        random_audit_id = f"id-{uuid.uuid4().hex}"
        random_metric = random.randint(500, 5000)
        
        audit_data = {
            "audit_id": random_audit_id,
            "portfolio_metric": random_metric,
            "description": "Integration test stress audit summary"
        }

        target_file = os.path.join(self.test_dir.name, "subfolder", f"target_{uuid.uuid4().hex}.json")

        proc_result = market_portfolio_stress_audit_summary_vault_process(target_file, audit_data)
        
        self.assertEqual(proc_result["status"], "saved")
        self.assertEqual(proc_result["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(target_file))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(target_file, random_audit_id)
        self.assertTrue(is_valid)

        invalid_check = market_portfolio_stress_audit_summary_vault_validate(target_file, "wrong-audit-id")
        self.assertFalse(invalid_check)

        export_result = market_portfolio_stress_audit_summary_vault_export(target_file, format="json")
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], random_audit_id)
        self.assertEqual(export_result["data"]["portfolio_metric"], random_metric)

if __name__ == "__main__":
    unittest.main()