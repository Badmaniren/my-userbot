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

class DummyDbStorage:
    def __init__(self, save_return_value):
        self.save_return_value = save_return_value

    def save(self, payload):
        return self.save_return_value

class DummyExtractor:
    def __init__(self):
        self.extracted = False

    def extract(self):
        self.extracted = True

class DummyMarketParser:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True

class DummyStressReporter:
    def __init__(self, payload):
        self.payload = payload

    def generate(self):
        return self.payload

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

    def test_start_new_integration_flow(self):
        expected_save_res = str(uuid.uuid4())
        db_storage = DummyDbStorage(save_return_value=expected_save_res)
        extractor = DummyExtractor()
        market_parser = DummyMarketParser()
        
        random_audit_id = str(uuid.uuid4())
        random_metric_value = float(uuid.uuid4().int & (1 << 32 - 1)) / 10**8
        payload = {
            "audit_id": random_audit_id,
            "metric": random_metric_value,
            "status": "stress_tested"
        }
        stress_reporter = DummyStressReporter(payload=payload)

        kwargs = {
            "db_storage": db_storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": market_parser,
            "market_portfolio_stress_reporter": stress_reporter
        }

        result = start_new(**kwargs)

        self.assertTrue(extractor.extracted, "Extractor dependency must be executed.")
        self.assertTrue(market_parser.parsed, "Market parser dependency must be executed.")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["save_result"], expected_save_res)
        self.assertEqual(result["payload"]["audit_id"], random_audit_id)
        self.assertEqual(result["payload"]["metric"], random_metric_value)

    def test_process_validate_export_integration_cycle(self):
        random_audit_id = str(uuid.uuid4())
        random_payload_value = str(uuid.uuid4())
        storage_target = os.path.join(self.test_dir.name, f"audit_{random_audit_id}.json")

        audit_data = {
            "audit_id": random_audit_id,
            "data_payload": random_payload_value,
            "details": {
                "risk_score": 0.85
            }
        }

        process_result = market_portfolio_stress_audit_summary_vault_process(storage_target, audit_data)
        
        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(storage_target), "Storage target file must be created on disk.")

        is_valid = market_portfolio_stress_audit_summary_vault_validate(storage_target, random_audit_id)
        self.assertTrue(is_valid, "Validation must return True for matching audit_id.")

        wrong_audit_id = str(uuid.uuid4())
        is_invalid = market_portfolio_stress_audit_summary_vault_validate(storage_target, wrong_audit_id)
        self.assertFalse(is_invalid, "Validation must return False for mismatched audit_id.")

        export_result = market_portfolio_stress_audit_summary_vault_export(storage_target, format="json")
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], random_audit_id)
        self.assertEqual(export_result["data"]["data_payload"], random_payload_value)

if __name__ == "__main__":
    unittest.main()