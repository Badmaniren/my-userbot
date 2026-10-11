import unittest
import os
import json
import uuid
import random

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealDatabaseStorage:
    def __init__(self, target_path):
        self.target_path = target_path

    def save(self, payload):
        dirname = os.path.dirname(self.target_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return {"status": "persisted", "path": self.target_path}

class RealExtractorTool:
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
    def __init__(self, audit_id):
        self.audit_id = audit_id

    def generate(self):
        return {
            "audit_id": self.audit_id,
            "metric_score": random.uniform(10.0, 100.0),
            "status": "audited"
        }

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    
    def setUp(self):
        self.random_str = uuid.uuid4().hex[:8]
        self.storage_filename = f"test_audit_storage_{self.random_str}.json"
        self.db_storage = RealDatabaseStorage(self.storage_filename)
        self.audit_id = f"AUDIT-{random.randint(1000, 9999)}-{self.random_str}"

    def tearDown(self):
        if os.path.exists(self.storage_filename):
            os.remove(self.storage_filename)

    def test_full_integration_pipeline(self):
        extractor = RealExtractorTool()
        parser = RealMarketParser()
        reporter = RealStressReporter(self.audit_id)

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
        self.assertEqual(result["payload"]["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(self.storage_filename))

        process_target = f"process_target_{self.random_str}.json"
        try:
            audit_data = {
                "audit_id": self.audit_id,
                "data": random.randint(1, 100)
            }
            process_res = market_portfolio_stress_audit_summary_vault_process(process_target, audit_data)
            self.assertEqual(process_res["status"], "saved")
            self.assertEqual(process_res["audit_id"], self.audit_id)

            is_valid = market_portfolio_stress_audit_summary_vault_validate(process_target, self.audit_id)
            self.assertTrue(is_valid)

            export_res = market_portfolio_stress_audit_summary_vault_export(process_target, format="json")
            self.assertEqual(export_res["format"], "json")
            self.assertEqual(export_res["data"]["audit_id"], self.audit_id)
        finally:
            if os.path.exists(process_target):
                os.remove(process_target)

if __name__ == "__main__":
    unittest.main()