import unittest
import os
import tempfile
import uuid
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
        market_portfolio_stress_audit_summary_vault_process(self.target_path, payload)
        return {"saved_to": self.target_path}

class RealDummyExtractor:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True

class RealDummyMarketParser:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True

class RealDummyStressReporter:
    def __init__(self, audit_id):
        self.audit_id = audit_id

    def generate(self):
        return {
            "audit_id": self.audit_id,
            "metric": str(uuid.uuid4()),
            "status": "completed"
        }

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_filename = f"audit_{uuid.uuid4().hex}.json"
        self.storage_target = os.path.join(self.test_dir.name, self.storage_filename)
        self.expected_audit_id = str(uuid.uuid4())

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_audit_lifecycle_integration(self):
        db_storage = RealDummyDbStorage(self.storage_target)
        extractor = RealDummyExtractor()
        market_parser = RealDummyMarketParser()
        stress_reporter = RealDummyStressReporter(self.expected_audit_id)

        kwargs = {
            "db_storage": db_storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": market_parser,
            "market_portfolio_stress_reporter": stress_reporter
        }

        result = start_new(**kwargs)

        self.assertEqual(result["status"], "success")
        self.assertIn("save_result", result)
        self.assertEqual(result["payload"]["audit_id"], self.expected_audit_id)
        self.assertTrue(extractor.extracted)
        self.assertTrue(market_parser.parsed)

        self.assertTrue(os.path.exists(self.storage_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            self.storage_target, self.expected_audit_id
        )
        self.assertTrue(is_valid)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            self.storage_target, format="json"
        )
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], self.expected_audit_id)
        self.assertEqual(export_result["data"]["status"], "completed")

    def test_validation_failure_on_wrong_id(self):
        db_storage = RealDummyDbStorage(self.storage_target)
        stress_reporter = RealDummyStressReporter(self.expected_audit_id)

        kwargs = {
            "db_storage": db_storage,
            "market_portfolio_stress_reporter": stress_reporter
        }

        start_new(**kwargs)

        wrong_id = str(uuid.uuid4())
        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            self.storage_target, wrong_id
        )
        self.assertFalse(is_valid)

if __name__ == "__main__":
    unittest.main()