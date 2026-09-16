import uuid
import json
import os

from skills.incident_financial_impact_evaluator import IncidentFinancialImpactEvaluator
from skills.incident_impact_analyzer import IncidentImpactAnalyzer


class IncidentBusinessLossReporter:
    def __init__(self, financial_evaluator=None, impact_analyzer=None):
        self.financial_evaluator = financial_evaluator or IncidentFinancialImpactEvaluator()
        self.impact_analyzer = impact_analyzer or IncidentImpactAnalyzer()

    def generate_report(self, incident_id, financial_data=None, export_path=None):
        if not incident_id:
            raise ValueError("Invalid incident_id")

        if financial_data is not None:
            fin_data = financial_data
        elif self.financial_evaluator:
            fin_data = self.financial_evaluator.evaluate(incident_id)
        else:
            fin_data = {}

        try:
            impact_data = self.impact_analyzer.analyze(incident_id) if self.impact_analyzer else {}
        except AttributeError:
            impact_data = self.impact_analyzer.analyze({"incident_id": incident_id}) if self.impact_analyzer else {}

        total_loss = fin_data.get("total_loss") if isinstance(fin_data, dict) else fin_data

        report = {
            "report_id": uuid.uuid4().hex,
            "incident_id": incident_id,
            "financial_loss": fin_data,
            "impact_details": impact_data,
            "total_loss": total_loss if total_loss is not None else 0.0
        }

        if export_path:
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=4)

        return report

    def export_report(self, report, format_type):
        if format_type not in ["json", "csv"]:
            raise ValueError("Unsupported format")
        report_id = report.get("report_id", uuid.uuid4().hex)
        return f"export_{report_id}.{format_type}"