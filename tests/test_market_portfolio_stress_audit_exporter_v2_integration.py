import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class RealDummyDB:
    def fetch_audit(self, audit_id):
        if audit_id == "not_found":
            return None
        return {"audit_id": audit_id, "risk_metric": random.randint(1, 100)}

class RealDummyExtractor:
    def extract(self, audit_id):
        return {"audit_id": audit_id, "payload_type": "anomaly"}

class RealDummyDetector:
    def evaluate(self, payload):
        return {"status": "evaluated", "audit_id": payload.get("audit_id")}

class RealDummyReporter:
    def generate_report(self, audit_data, export_format):
        return json.dumps(audit_data).encode("utf-8")

class RealDummyVault:
    def load_summary(self, audit_id):
        import io
        return io.BytesIO(b"summary_data")

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):
    def setUp(self):
        self.db = RealDummyDB()
        self.ext1 = RealDummyExtractor()
        self.ext2 = RealDummyExtractor()
        self.detector = RealDummyDetector()
        self.reporter = RealDummyReporter()
        self.vault = RealDummyVault()
        self.generator = None

        self.exporter = MarketPortfolioStressAuditExporterV2(
            db_storage=self.db,
            extractor_tool_1790087207=self.ext1,
            extractor_tool_1790102839=self.ext2,
            market_anomaly_detector=self.detector,
            market_portfolio_stress_reporter=self.reporter,
            market_portfolio_stress_audit_summary_vault=self.vault,
            market_report_generator=self.generator
        )

    def test_export_report_integration(self):
        audit_id = str(uuid.uuid4())
        rand_val = random.randint(1000, 9999)
        dest_path = f"/tmp/test_audit_report_{rand_val}.json"

        if os.path.exists(dest_path):
            os.remove(dest_path)

        try:
            success = self.exporter.export_report(audit_id, "json", dest_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(dest_path))

            with open(dest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data["audit_id"], audit_id)
        finally:
            if os.path.exists(dest_path):
                os.remove(dest_path)

    def test_main_function_integration(self):
        run_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        stress_factor = round(random.uniform(0.1, 0.9), 2)

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        result = market_portfolio_stress_audit_exporter_v2_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)

        export_path = result["export_path"]
        self.assertTrue(os.path.exists(export_path))

        try:
            with open(export_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data["run_id"], run_id)
                self.assertEqual(saved_data["portfolio_id"], portfolio_id)
                self.assertEqual(saved_data["stress_factor"], stress_factor)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

if __name__ == "__main__":
    unittest.main()