import unittest
import os
import uuid
import json
import io
from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class RealDummyDBStorage:
    def fetch_audit(self, audit_id: str):
        if audit_id == "not_found":
            return None
        return {"audit_id": audit_id, "data": "test_audit_payload"}

class RealDummyExtractor1:
    def extract(self, audit_id: str):
        return {"audit_id": audit_id, "metric": "anomaly_score", "value": 99.9}

class RealDummyExtractor2:
    def extract(self, audit_id: str):
        return {"audit_id": audit_id, "secondary": True}

class RealDummyAnomalyDetector:
    def evaluate(self, payload: dict):
        return {"status": "anomaly_detected", "payload": payload}

class RealDummyReporter:
    def generate_report(self, audit_data: dict, export_format: str) -> bytes:
        return f"REPORT:{audit_data['audit_id']}:{export_format}".encode("utf-8")

class RealDummyVault:
    def load_summary(self, audit_id: str) -> io.BytesIO:
        return io.BytesIO(f"SUMMARY:{audit_id}".encode("utf-8"))

class RealDummyReportGen:
    def generate(self, *args, **kwargs):
        return True

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def setUp(self):
        self.db_storage = RealDummyDBStorage()
        self.extractor_1 = RealDummyExtractor1()
        self.extractor_2 = RealDummyExtractor2()
        self.anomaly_detector = RealDummyAnomalyDetector()
        self.reporter = RealDummyReporter()
        self.vault = RealDummyVault()
        self.report_gen = RealDummyReportGen()

        self.exporter = MarketPortfolioStressAuditExporterV2(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_stress_reporter=self.reporter,
            market_portfolio_stress_audit_summary_vault=self.vault,
            market_report_generator=self.report_gen
        )
        self.test_files = []

    def tearDown(self):
        for file_path in self.test_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_export_report_integration(self):
        audit_id = str(uuid.uuid4())
        export_format = "json"
        dest_path = f"/tmp/test_audit_{uuid.uuid4()}.dat"
        self.test_files.append(dest_path)

        success = self.exporter.export_report(audit_id, export_format, dest_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(dest_path))
        
        with open(dest_path, "rb") as f:
            content = f.read()
        
        expected_content = f"REPORT:{audit_id}:{export_format}".encode("utf-8")
        self.assertEqual(content, expected_content)

    def test_export_report_not_found(self):
        with self.assertRaises(ValueError):
            self.exporter.export_report("not_found", "json", "/tmp/should_not_exist.dat")

    def test_stream_audit_summary_integration(self):
        audit_id = str(uuid.uuid4())
        stream = self.exporter.stream_audit_summary(audit_id)
        
        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read().decode("utf-8")
        self.assertEqual(content, f"SUMMARY:{audit_id}")

    def test_main_function_integration(self):
        run_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        stress_factor = float(uuid.uuid4().int % 100) / 10.0

        payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }

        expected_path = f"/tmp/{run_id}.json"
        self.test_files.append(expected_path)

        result = market_portfolio_stress_audit_exporter_v2_main(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["export_path"], expected_path)

        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["run_id"], run_id)
        self.assertEqual(data["portfolio_id"], portfolio_id)
        self.assertEqual(data["stress_factor"], stress_factor)
        self.assertEqual(data["status"], "success")

if __name__ == "__main__":
    unittest.main()