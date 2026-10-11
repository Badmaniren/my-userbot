import unittest
import os
import tempfile
import uuid
import json

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealDatabaseStorageStub:
    def __init__(self):
        self.saved_payloads = []

    def save(self, payload):
        self.saved_payloads.append(payload)
        return {"saved_status": "ok", "records_count": len(payload)}

class RealMarketParserStub:
    def __init__(self):
        self.parsed = False

    def parse_stream(self):
        self.parsed = True

class RealStressReporterStub:
    def __init__(self, data_dict):
        self.data_dict = data_dict

    def generate(self):
        return self.data_dict

class IntegrationMarketPortfolioStressAuditTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_id = str(uuid.uuid4())
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = float(uuid.uuid4().int % 10000) / 100.0

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_stress_audit_integration_cycle(self):
        db_storage = RealDatabaseStorageStub()
        market_parser = RealMarketParserStub()
        
        expected_payload = {
            "audit_id": self.audit_id,
            "metric": self.metric_name,
            "value": self.metric_value,
            "status": "stress_tested"
        }
        stress_reporter = RealStressReporterStub(expected_payload)

        start_result = start_new(
            db_storage=db_storage,
            market_parser=market_parser,
            market_portfolio_stress_reporter=stress_reporter
        )

        self.assertEqual(start_result["status"], "success")
        self.assertEqual(start_result["payload"]["audit_id"], self.audit_id)
        self.assertTrue(market_parser.parsed)
        self.assertIn(expected_payload, db_storage.saved_payloads)

        storage_target = os.path.join(self.test_dir.name, f"audit_{self.audit_id}.json")
        
        process_result = market_portfolio_stress_audit_summary_vault_process(
            storage_target=storage_target,
            audit_data=expected_payload
        )

        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], self.audit_id)
        self.assertTrue(os.path.exists(storage_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            storage_target=storage_target,
            expected_audit_id=self.audit_id
        )
        self.assertTrue(is_valid)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            storage_target=storage_target,
            format="json"
        )

        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], self.audit_id)
        self.assertEqual(export_result["data"]["metric"], self.metric_name)
        self.assertEqual(export_result["data"]["value"], self.metric_value)

if __name__ == "__main__":
    unittest.main()