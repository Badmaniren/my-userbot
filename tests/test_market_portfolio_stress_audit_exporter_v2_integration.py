import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class RealDummyDBStorage:
    def fetch_audit(self, audit_id: str):
        if audit_id == "not_found":
            return None
        return {"audit_id": audit_id, "data": "valid_test_data"}

class RealDummyExtractor:
    def __init__(self, audit_id_to_return):
        self.audit_id_to_return = audit_id_to_return
    def extract(self, audit_id: str):
        return {"extracted_audit_id": self.audit_id_to_return}

class RealDummyAnomalyDetector:
    def evaluate(self, payload: dict):
        return {"status": "evaluated", "payload": payload}

class RealDummyReporter:
    def generate_report(self, audit_data: dict, export_format: str) -> bytes:
        return f"REPORT_{audit_data['audit_id']}_{export_format}".encode("utf-8")

class RealDummyVault:
    def load_summary(self, audit_id: str):
        import io
        return io.BytesIO(f"SUMMARY_{audit_id}".encode("utf-8"))

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def setUp(self):
        self.db_storage = RealDummyDBStorage()
        self.rand_id = str(uuid.uuid4())
        self.extractor_1 = RealDummyExtractor(self.rand_id)
        self.extractor_2 = RealDummyExtractor(self.rand_id)
        self.anomaly_detector = RealDummyAnomalyDetector()
        self.reporter = RealDummyReporter()
        self.vault = RealDummyVault()
        self.generator = None

        self.exporter = MarketPortfolioStressAuditExporterV2(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_stress_reporter=self.reporter,
            market_portfolio_stress_audit_summary_vault=self.vault,
            market_report_generator=self.generator
        )

    def test_export_report_integration(self):
        export_format = random.choice(["json", "csv", "pdf", "xml"])
        dest_path = f"/tmp/test_audit_report_{uuid.uuid4()}.{export_format}"
        
        try:
            result = self.exporter.export_report(self.rand_id, export_format, dest_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(dest_path))
            
            with open(dest_path, "rb") as f:
                content = f.read()
            self.assertIn(self.rand_id.encode("utf-8"), content)
            self.assertIn(export_format.encode("utf-8"), content)
        finally:
            if os.path.exists(dest_path):
                os.remove(dest_path)

    def test_export_report_not_found(self):
        with self.assertRaises(ValueError):
            self.exporter.export_report("not_found", "json", "/tmp/should_not_exist.json")

    def test_stream_audit_summary_integration(self):
        stream = self.exporter.stream_audit_summary(self.rand_id)
        content = stream.read()
        self.assertIn(self.rand_id.encode("utf-8"), content)

    def test_main_function_integration(self):
        run_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        stress_factor = round(random.uniform(1.0, 100.0), 2)

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        expected_path = f"/tmp/{run_id}.json"
        
        try:
            res = market_portfolio_stress_audit_exporter_v2_main(payload)
            
            self.assertEqual(res.get("status"), "success")
            self.assertEqual(res.get("run_id"), run_id)
            self.assertEqual(res.get("portfolio_id"), portfolio_id)
            self.assertEqual(res.get("export_path"), expected_path)
            
            self.assertTrue(os.path.exists(expected_path))
            
            with open(expected_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.assertEqual(data.get("run_id"), run_id)
            self.assertEqual(data.get("portfolio_id"), portfolio_id)
            self.assertEqual(data.get("stress_factor"), stress_factor)
            self.assertEqual(data.get("status"), "success")
        finally:
            if os.path.exists(expected_path):
                os.remove(expected_path)

if __name__ == "__main__":
    unittest.main()