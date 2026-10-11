from datetime import datetime
import io
import requests

from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_stress_audit_exporter_v2 import market_portfolio_stress_audit_exporter_v2
from skills.db_storage import db_storage

class MarketPortfolioRegulatoryReportingFeed:
    def __init__(self, db_storage=None, market_portfolio_stress_audit_summary_vault=None,
                 market_portfolio_stress_audit_exporter_v2=None, market_report_generator=None):
        self.db_storage = db_storage
        self.summary_vault = market_portfolio_stress_audit_summary_vault
        self.exporter_v2 = market_portfolio_stress_audit_exporter_v2
        self.report_generator = market_report_generator

    def generate_feed(self, report_id):
        audit_summary = self.summary_vault.fetch_latest_audit_summary()
        if not audit_summary:
            raise ValueError("Audit summary data is missing")

        export_res = self.exporter_v2.export_v2_format(audit_summary)

        timestamp = datetime.utcnow().isoformat()

        result = {
            "report_id": report_id,
            "audit_reference": audit_summary.get("audit_hash"),
            "timestamp": timestamp,
            "export_status": export_res.get("status")
        }

        if self.db_storage and hasattr(self.db_storage, "save_regulatory_feed_log"):
            self.db_storage.save_regulatory_feed_log(result)

        return result

    def validate_feed_stream(self, feed_stream):
        stream_content = feed_stream.read()
        response = requests.post("https://api.regulatory-compliance.internal/validate", data=stream_content)
        if response.status_code == 200:
            data = response.json()
            return data.get("validated", False)
        return False

    def export_regulatory_package(self, filename):
        pdf_stream = self.report_generator.render_pdf(filename)
        return pdf_stream.read()


def market_portfolio_regulatory_reporting_feed(feed_payload):
    run_id = feed_payload.get("run_id")

    audit_data = {
        "run_id": run_id,
        "portfolio_id": feed_payload.get("portfolio_id"),
        "report_type": feed_payload.get("report_type")
    }
    market_portfolio_stress_audit_summary_vault(audit_data)

    export_config = {
        "run_id": run_id,
        "format": "v2",
        "destination": f"./test_export_{run_id}.json"
    }
    market_portfolio_stress_audit_exporter_v2(export_config)

    db_storage("INSERT INTO regulatory_feeds (run_id) VALUES (?)", (run_id,))

    return {
        "status": "SUCCESS",
        "run_id": run_id
    }