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

class RealDbStorageStub:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def save(self, payload):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            import json
            json.dump(payload, f)
        return {"status": "saved_by_db_storage", "path": self.storage_path}

class RealStressReporterStub:
    def __init__(self, payload):
        self.payload = payload

    def generate(self):
        return self.payload

class TestMarketPortfolioStressAuditSummaryVaultIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.target_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_full_workflow_without_mocks(self):
        random_audit_id = f"audit-id-{uuid.uuid4()}"
        random_score = random.uniform(10.0, 99.9)
        
        audit_payload = {
            "audit_id": random_audit_id,
            "score": random_score,
            "metrics": {
                "var": random.randint(1000, 50000),
                "status": "stable"
            }
        }

        db_storage = RealDbStorageStub(self.target_file)
        stress_reporter = RealStressReporterStub(audit_payload)

        start_result = start_new(
            db_storage=db_storage,
            market_portfolio_stress_reporter=stress_reporter
        )

        self.assertEqual(start_result["status"], "success")
        self.assertEqual(start_result["payload"]["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(self.target_file))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            self.target_file, 
            random_audit_id
        )
        self.assertTrue(is_valid)

        export_result = market_portfolio_stress_audit_summary_vault_export(
            self.target_file, 
            format="json"
        )
        self.assertEqual(export_result["format"], "json")
        self.assertEqual(export_result["data"]["audit_id"], random_audit_id)
        self.assertEqual(export_result["data"]["score"], random_score)

        new_target_file = os.path.join(self.test_dir.name, f"sub_{uuid.uuid4()}/processed_{uuid.uuid4()}.json")
        process_result = market_portfolio_stress_audit_summary_vault_process(
            new_target_file, 
            audit_payload
        )

        self.assertEqual(process_result["status"], "saved")
        self.assertEqual(process_result["audit_id"], random_audit_id)
        self.assertTrue(os.path.exists(new_target_file))

        self.assertTrue(
            market_portfolio_stress_audit_summary_vault_validate(new_target_file, random_audit_id)
        )

if __name__ == "__main__":
    unittest.main()