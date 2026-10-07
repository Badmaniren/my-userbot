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

class RealDummyStorage:
    def __init__(self, target_path):
        self.target_path = target_path

    def save(self, payload):
        market_portfolio_stress_audit_summary_vault_process(self.target_path, payload)
        return {"path": self.target_path, "saved": True}

class RealDummyExtractor:
    def extract(self):
        pass

class RealDummyParser:
    def parse_stream(self):
        pass

class RealDummyReporter:
    def __init__(self, audit_id):
        self.audit_id = audit_id

    def generate(self):
        return {
            "audit_id": self.audit_id,
            "metric": str(uuid.uuid4())
        }

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.target_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_workflow(self):
        expected_id = str(uuid.uuid4())
        storage = RealDummyStorage(self.target_file)
        extractor = RealDummyExtractor()
        parser = RealDummyParser()
        reporter = RealDummyReporter(expected_id)

        kwargs = {
            "db_storage": storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": parser,
            "market_portfolio_stress_reporter": reporter
        }

        result = start_new(**kwargs)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"]["audit_id"], expected_id)

        is_valid = market_portfolio_stress_audit_summary_vault_validate(self.target_file, expected_id)
        self.assertTrue(is_valid)

        export_res = market_portfolio_stress_audit_summary_vault_export(self.target_file, format="json")
        self.assertEqual(export_res["format"], "json")
        self.assertEqual(export_res["data"]["audit_id"], expected_id)

        invalid_check = market_portfolio_stress_audit_summary_vault_validate(self.target_file, "wrong-id-")
        self.assertFalse(invalid_check)

if __name__ == "__main__":
    unittest.main()