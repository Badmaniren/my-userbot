import json
import io
from skills.incident_financial_impact_evaluator import incident_financial_impact_evaluator
from skills.incident_impact_analyzer import incident_impact_analyzer

class IncidentBusinessLossReporter:
    def __init__(self, financial_evaluator=None, impact_analyzer=None):
        if financial_evaluator is not None:
            self.financial_evaluator = financial_evaluator
        else:
            try:
                self.financial_evaluator = incident_financial_impact_evaluator()
            except TypeError:
                self.financial_evaluator = incident_financial_impact_evaluator

        if impact_analyzer is not None:
            self.impact_analyzer = impact_analyzer
        else:
            try:
                self.impact_analyzer = incident_impact_analyzer()
            except TypeError:
                self.impact_analyzer = incident_impact_analyzer

    def generate_report(self, incident_id, export_path=None, financial_impact=None, impact_analysis=None):
        if financial_impact is not None:
            financial_data = financial_impact
        else:
            if callable(getattr(self.financial_evaluator, "evaluate", None)):
                financial_data = self.financial_evaluator.evaluate(incident_id)
            elif callable(self.financial_evaluator):
                financial_data = self.financial_evaluator(incident_id)
            else:
                financial_data = {}

        if impact_analysis is not None:
            impact_data = impact_analysis
        else:
            if callable(getattr(self.impact_analyzer, "analyze", None)):
                impact_data = self.impact_analyzer.analyze(incident_id)
            elif callable(self.impact_analyzer):
                impact_data = self.impact_analyzer(incident_id).analyze(incident_id) if hasattr(self.impact_analyzer(incident_id), "analyze") else self.impact_analyzer(incident_id)
            else:
                impact_data = {}

        currency = financial_data.get("currency", "USD")
        total_loss = financial_data.get("total_loss", financial_data.get("direct_financial_loss", 0.0))

        report = {
            "report_id": financial_data.get("report_id", incident_id),
            "incident_id": incident_id,
            "currency": currency,
            "total_loss": total_loss,
            "financial_metrics": {
                "total_loss": total_loss,
                "direct_financial_loss": financial_data.get("direct_financial_loss", 0.0),
                "indirect_financial_loss": financial_data.get("indirect_financial_loss", 0.0)
            },
            "impact_metrics": {
                "downtime_minutes": impact_data.get("downtime_minutes", 0),
                "affected_services_count": impact_data.get("affected_services_count", 0),
                "severity_level": impact_data.get("severity_level", "MEDIUM")
            },
            "is_generated": True,
            "details": financial_data.get("details")
        }

        if export_path:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f)
            report["export_status"] = "success"

        return report

    def _aggregate_losses(self, sub_evaluators_data, key="loss"):
        return sum(item.get(key, 0.0) for item in sub_evaluators_data)

    def generate_stream_report(self, incident_id):
        report = self.generate_report(incident_id)
        stream = io.BytesIO(json.dumps(report).encode('utf-8'))
        return stream


def incident_business_loss_reporter():
    return IncidentBusinessLossReporter()