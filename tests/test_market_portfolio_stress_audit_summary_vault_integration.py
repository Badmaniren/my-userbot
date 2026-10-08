import unittest
import os
import uuid
import json
from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate,
    market_portfolio_stress_audit_summary_vault_export
)

class RealDbStorage:
    def __init__(self, saved_value):
        self.saved_value = saved_value
        self.last_saved = None

    def save(self, payload):
        self.last_saved = payload
        return self.saved_value

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
        self.generated = False

    def generate(self):
        self.generated = True
        return self.payload

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def test_start_new_integration_flow(self):
        unique_save_res = str(uuid.uuid4())
        expected_payload = {
            "audit_id": str(uuid.uuid4()),
            "metric": "value_" + str(uuid.uuid4())
        }
        
        db_storage = RealDbStorage(saved_value=unique_save_res)
        extractor = RealExtractor()
        market_parser = RealMarketParser()
        stress_reporter = RealStressReporter(payload=expected_payload)
        
        kwargs = {
            "db_storage": db_storage,
            "extractor_tool_1790087207": extractor,
            "market_parser": market_parser,
            "market_portfolio_stress_reporter": stress_reporter
        }
        
        result = start_new(**kwargs)
        
        self.assertTrue(extractor.extracted)
        self.assertTrue(market_parser.parsed)
        self.assertTrue(stress_reporter.generated)
        self.assertEqual(db_storage.last_saved, expected_payload)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("save_result"), unique_save_res)
        self.assertEqual(result.get("payload"), expected_payload)

    def test_storage_process_validate_and_export_flow(self):
        random_filename = f"test_audit_{uuid.uuid4()}.json"
        audit_id = str(uuid.uuid4())
        audit_data = {
            "audit_id": audit_id,
            "details": f"data_{uuid.uuid4()}"
        }
        
        try:
            process_res = market_portfolio_stress_audit_summary_vault_process(random_filename, audit_data)
            self.assertEqual(process_res.get("status"), "saved")
            self.assertEqual(process_res.get("audit_id"), audit_id)
            self.assertTrue(os.path.exists(random_filename))
            
            is_valid = market_portfolio_stress_audit_summary_vault_validate(random_filename, audit_id)
            self.assertTrue(is_valid)
            
            invalid_check = market_portfolio_stress_audit_summary_vault_validate(random_filename, "wrong-audit-id")
            self.assertFalse(invalid_check)
            
            export_res = market_portfolio_stress_audit_summary_vault_export(random_filename, format="json")
            self.assertEqual(export_res.get("format"), "json")
            self.assertEqual(export_res.get("data"), audit_data)
        finally:
            if os.path.exists(random_filename):
                os.remove(random_filename)
                dirname = os.path.dirname(random_filename)
                if dirname and os.path.exists(dirname) and not os.listdir(dirname):
                    os.rmdir(dirname)

if __name__ == "__main__":
    unittest.main()