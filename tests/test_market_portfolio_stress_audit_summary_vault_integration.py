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

class RealDbStorage:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def save(self, payload):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return {"saved_status": "ok", "path": self.storage_path}

class RealStressReporter:
    def __init__(self, data):
        self.data = data

    def generate(self):
        return self.data

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"vault_{uuid.uuid4().hex}.json")
        self.db_storage = RealDbStorage(self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_start_new_and_vault_lifecycle(self):
        unique_audit_id = f"audit-{uuid.uuid4()}"
        unique_scenario = f"scenario-{uuid.uuid4().hex[:8]}"
        
        payload_data = {
            "audit_id": unique_audit_id,
            "scenario": unique_scenario,
            "version": 1,
            "metrics": {
                "var_95": float(uuid.uuid4().int % 1000) / 10.0,
                "max_drawdown": float(uuid.uuid4().int % 500) / 10.0
            }
        }

        stress_reporter = RealStressReporter(payload_data)

        start_result = start_new(
            db_storage=self.db_storage,
            market_portfolio_stress_reporter=stress_reporter
        )

        self.assertEqual(start_result["status"], "success")
        self.assertEqual(start_result["payload"]["audit_id"], unique_audit_id)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, "r", encoding="utf-8") as f:
            saved_content = json.load(f)
        self.assertEqual(saved_content["audit_id"], unique_audit_id)
        self.assertEqual(saved_content["scenario"], unique_scenario)

        target_path = os.path.join(self.test_dir.name, f"target_{uuid.uuid4().hex}.json")
        process_result = market_portfolio_stress_audit_summary_vault_process(target_path, payload_data)
        
        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], unique_audit_id)
        self.assertTrue(os.path.exists(target_path))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(target_path, unique_audit_id)
        self.assertTrue(is_valid)

        is_invalid = market_portfolio_stress_audit_summary_vault_validate(target_path, "wrong-audit-id")
        self.assertFalse(is_invalid)

        export_res = market_portfolio_stress_audit_summary_vault_export(target_path, format="json")
        self.assertEqual(export_res["format"], "json")
        self.assertEqual(export_res["data"]["audit_id"], unique_audit_id)
        self.assertEqual(export_res["data"]["scenario"], unique_scenario)

if __name__ == "__main__":
    unittest.main()