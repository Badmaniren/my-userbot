import unittest
import uuid
import random
import os
import io
import json
from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class RealDbStorage:
    def __init__(self, data_store):
        self.data_store = data_store
    def fetch_audit(self, audit_id):
        return self.data_store.get(audit_id)

class RealExtractorTool:
    def __init__(self, data_store):
        self.data_store = data_store
    def extract(self, audit_id):
        return {"audit_id": audit_id, "payload_data": self.data_store.get(audit_id, {})}

class RealMarketAnomalyDetector:
    def evaluate(self, payload):
        return {"status": "evaluated", "payload": payload, "risk_score": random.uniform(0.0, 1.0)}

class RealMarketPortfolioStressReporter:
    def generate_report(self, audit_data, export_format):
        return json.dumps({"format": export_format, "data": audit_data}).encode("utf-8")

class RealMarketPortfolioStressAuditSummaryVault:
    def load_summary(self, audit_id):
        content = json.dumps({"summary_for": audit_id}).encode("utf-8")
        return io.BytesIO(content)

class RealMarketReportGenerator:
    def generate(self):
        return "report"

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def test_integration_flow_and_main(self):
        audit_id = str(uuid.uuid4())
        portfolio_id = str(uuid.uuid4())
        stress_factor = round(random.uniform(1.0, 10.0), 2)
        run_id = str(uuid.uuid4())
        destination_path = f"/tmp/{uuid.uuid4()}.json"

        stored_data = {"portfolio_id": portfolio_id, "metrics": [random.randint(1, 100)]}
        db_storage = RealDbStorage({audit_id: stored_data})
        extractor_1 = RealExtractorTool({audit_id: stored_data})
        extractor_2 = RealExtractorTool({audit_id: stored_data})
        anomaly_detector = RealMarketAnomalyDetector()
        stress_reporter = RealMarketPortfolioStressReporter()
        summary_vault = RealMarketPortfolioStressAuditSummaryVault()
        report_generator = RealMarketReportGenerator()

        exporter = MarketPortfolioStressAuditExporterV2(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor_1,
            extractor_tool_1790102839=extractor_2,
            market_anomaly_detector=anomaly_detector,
            market_portfolio_stress_reporter=stress_reporter,
            market_portfolio_stress_audit_summary_vault=summary_vault,
            market_report_generator=report_generator
        )

        export_result = exporter.export_report(audit_id, "json", destination_path)
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(destination_path))

        with open(destination_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)
        self.assertEqual(file_content["data"]["portfolio_id"], portfolio_id)

        os.remove(destination_path)

        summary_stream = exporter.stream_audit_summary(audit_id)
        self.assertIsInstance(summary_stream, io.BytesIO)
        summary_data = json.loads(summary_stream.getvalue().decode("utf-8"))
        self.assertEqual(summary_data["summary_for"], audit_id)

        main_payload = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "stress_factor": stress_factor
        }
        main_result = market_portfolio_stress_audit_exporter_v2_main(main_payload)

        self.assertEqual(main_result["status"], "success")
        self.assertEqual(main_result["run_id"], run_id)
        self.assertEqual(main_result["portfolio_id"], portfolio_id)
        
        expected_path = main_result["export_path"]
        self.assertTrue(os.path.exists(expected_path))

        with open(expected_path, "r", encoding="utf-8") as f:
            main_file_content = json.load(f)
        self.assertEqual(main_file_content["run_id"], run_id)
        self.assertEqual(main_file_content["stress_factor"], stress_factor)

        if os.path.exists(expected_path):
            os.remove(expected_path)

if __name__ == "__main__":
    unittest.main()