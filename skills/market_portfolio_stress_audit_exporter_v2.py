import io
import json
import os
try:
    import requests
except ImportError:
    requests = None


class MarketPortfolioStressAuditExporterV2:

    def __init__(
        self,
        db_storage,
        extractor_tool_1790087207,
        extractor_tool_1790102839,
        market_anomaly_detector,
        market_portfolio_stress_reporter,
        market_portfolio_stress_audit_summary_vault,
        market_report_generator
    ):
        self.db_storage = db_storage
        self.extractor_tool_1 = extractor_tool_1790087207
        self.extractor_tool_2 = extractor_tool_1790102839
        self.market_anomaly_detector = market_anomaly_detector
        self.market_portfolio_stress_reporter = market_portfolio_stress_reporter
        self.market_portfolio_stress_audit_summary_vault = market_portfolio_stress_audit_summary_vault
        self.market_report_generator = market_report_generator

    def export_report(self, audit_id: str, export_format: str, destination_path: str) -> bool:
        audit_data = self.db_storage.fetch_audit(audit_id)
        if audit_data is None:
            raise ValueError(f"Audit with id {audit_id} not found")
        
        content = self.market_portfolio_stress_reporter.generate_report(audit_data, export_format)
        
        with open(destination_path, "wb") as f:
            f.write(content)
            
        return os.path.exists(destination_path)

    def stream_audit_summary(self, audit_id: str) -> io.BytesIO:
        return self.market_portfolio_stress_audit_summary_vault.load_summary(audit_id)

    def process_and_dispatch_anomaly_audit(self, audit_id: str, webhook_url: str) -> bool:
        payload = self.extractor_tool_1.extract(audit_id)
        evaluation = self.market_anomaly_detector.evaluate(payload)
        
        response = requests.post(webhook_url, json=evaluation)
        return response.status_code == 200


def export(stream_data) -> str:
    export_path = f"/tmp/export_{hash(str(stream_data)) & 0xffffffff}.json"
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump({"stream": stream_data}, f)
    return export_path


def market_portfolio_stress_audit_exporter_v2_main(payload: dict) -> dict:
    run_id = payload.get("run_id")
    portfolio_id = payload.get("portfolio_id")
    stress_factor = payload.get("stress_factor")
    
    export_path = f"/tmp/{run_id}.json"
    
    report_data = {
        "run_id": run_id,
        "portfolio_id": portfolio_id,
        "stress_factor": stress_factor,
        "status": "success"
    }
    
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f)
        
    return {
        "status": "success",
        "run_id": run_id,
        "portfolio_id": portfolio_id,
        "export_path": export_path
    }