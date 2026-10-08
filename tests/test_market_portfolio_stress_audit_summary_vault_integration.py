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

class RealRealDbStorage:
    def __init__(self):
        self.saved_data = []

    def save(self, payload):
        self.saved_data.append(payload)
        return {"saved_count": len(self.saved_data), "last_payload": payload}

class RealRealExtractor:
    def __init__(self, name):
        self.name = name
        self.extracted = False

    def extract(self):
        self.extracted = True
        return {self.name: "extracted_data"}

class RealRealParser:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True
        return {"parsed": True}

class RealRealStressReporter:
    def __init__(self, data):
        self.data = data

    def generate(self):
        return self.data

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_id = str(uuid.uuid4())
        self.random_value = random.randint(1000, 9999)
        self.storage_target = os.path.join(self.test_dir.name, f"audit_{self.audit_id}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_start_new_full_pipeline(self):
        db_storage = RealRealDbStorage()
        extractor = RealRealExtractor(f"ext_{self.random_value}")
        parser = RealRealParser()
        
        expected_payload = {
            "audit_id": self.audit_id,
            "metric": self.random_value,
            "status": "stress_tested"
        }
        stress_reporter = RealRealStressReporter(expected_payload)

        kwargs = {
            "db_storage": db_storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": parser,
            "market_portfolio_stress_reporter": stress_reporter
        }

        result = start_new(**kwargs)

        self.assertTrue(extractor.extracted)
        self.assertTrue(parser.parsed)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["payload"], expected_payload)
        self.assertEqual(len(db_storage.saved_data), 1)
        self.assertEqual(db_storage.saved_data[0], expected_payload)

    def test_integration_storage_process_validate_export(self):
        audit_data = {
            "audit_id": self.audit_id,
            "score": self.random_value,
            "details": "Integration audit payload verification"
        }

        process_result = market_portfolio_stress_audit_summary_vault_process(
            storage_target=self.storage_target,
            audit_data=audit_data
        )

        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(self.storage_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=self.storage_target,
            expected_audit_id=self.audit_id
        )
        self.assertTrue(is_valid)

        invalid_check = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=self.storage_target,
            expected_audit_id=str(uuid.uuid4())
        )
        self.assertFalse(invalid_check)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            storage_target=self.storage_target,
            format="json"
        )
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"], audit_data)

if __name__ == "__main__":
    unittest.main()