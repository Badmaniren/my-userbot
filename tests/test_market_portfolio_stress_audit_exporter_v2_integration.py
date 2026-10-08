import unittest
import os
import uuid
import json
import io
from skills.market_portfolio_stress_audit_exporter_v2 import (
    MarketPortfolioStressAuditExporterV2,
    market_portfolio_stress_audit_exporter_v2_main
)

class RealDatabaseStorageStub:
    def __init__(self, data):
        self.data = data
    def fetch_audit(self, audit_id):
        return self.data.get(audit_id)

class RealExtractorToolStub:
    def __init__(self, payload):
        self.payload = payload
    def extract(self, audit_id):
        return {"audit_id": audit_id, "data": self.payload}

class RealAnomalyDetectorStub:
    def evaluate(self, payload):
        return {"status": "analyzed", "payload": payload}

class RealStressReporterStub:
    def generate_report(self, audit_data, export_format):
        return f"REPORT:{audit_data['name']}:{export_format}".encode("utf-8")

class RealSummaryVaultStub:
    def __init__(self, content):
        self.content = content
    def load_summary(self, audit_id):
        return io.BytesIO(self.content)

class TestMarketPortfolioStressAuditExporterV2Integration(unittest.TestCase):

    def test_export_report_and_main_flow(self):
        unique_run_id = str(uuid.uuid4())
        unique_portfolio_id = str(uuid.uuid4())
        stress_val = round(float(uuid.uuid1().int & 0xFF) / 10.0, 2)
        
        payload = {
            "run_id": unique_run_id,
            "portfolio_id": unique_portfolio_id,
            "stress_factor": stress_val
        }

        result = market_portfolio_stress_audit_exporter_v2_main(payload)
        
        self.assertEqual(result["run_id"], unique_run_id)
        self.assertEqual(result["portfolio_id"], unique_portfolio_id)
        self.assertEqual(result["status"], "success")
        
        export_path = result["export_path"]
        self.assertTrue(os.path.exists(export_path))
        
        with open(export_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["run_id"], unique_run_id)
            self.assertEqual(file_data["stress_factor"], stress_val)
            
        if os.path.exists(export_path):
            os.remove(export_path)

    def test_exporter_class_integration(self):
        audit_id = str(uuid.uuid4())
        audit_name = f"audit_{uuid.uuid4()}"
        export_format = "CSV"
        dest_path = f"/tmp/test_report_{uuid.uuid4()}.csv"
        
        db = RealDatabaseStorageStub({audit_id: {"name": audit_name}})
        ext1 = RealExtractorToolStub("test_payload")
        detector = RealAnomalyDetectorStub()
        reporter = RealStressReporterStub()
        vault = RealSummaryVaultStub(b"summary_bytes")
        
        exporter = MarketPortfolioStressAuditExporterV2(
            db_storage=db,
            extractor_tool_1790087207=ext1,
            extractor_tool_1790102839=ext1,
            market_anomaly_detector=detector,
            market_portfolio_stress_reporter=reporter,
            market_portfolio_stress_audit_summary_vault=vault,
            market_report_generator=None
        )
        
        success = exporter.export_report(audit_id, export_format, dest_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(dest_path))
        
        with open(dest_path, "rb") as f:
            content = f.read()
            self.assertEqual(content, f"REPORT:{audit_name}:{export_format}".encode("utf-8"))
            
        summary_stream = exporter.stream_audit_summary(audit_id)
        self.assertEqual(summary_stream.read(), b"summary_bytes")
        
        if os.path.exists(dest_path):
            os.remove(dest_path)

if __name__ == "__main__":
    unittest.main()