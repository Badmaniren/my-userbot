import os
import io
from skills.incident_impact_analyzer import IncidentImpactAnalyzer

class IncidentFinancialImpactEvaluator:
    def evaluate(self, incident_id_or_impact_data):
        try:
            if isinstance(incident_id_or_impact_data, dict):
                impact_data = incident_id_or_impact_data
                incident_id = impact_data.get("incident_id")
            else:
                incident_id = incident_id_or_impact_data
                analyzer = IncidentImpactAnalyzer()
                impact_data = analyzer.get_impact_data(incident_id)

            if impact_data is None:
                raise ValueError("Impact data is missing or None")

            if not isinstance(impact_data, dict):
                raise ValueError("Impact data must be a dictionary")

            downtime_hours = impact_data.get("downtime_hours")
            if downtime_hours is None and "downtime_minutes" in impact_data:
                try:
                    downtime_minutes = float(impact_data["downtime_minutes"])
                    downtime_hours = downtime_minutes / 60.0
                except (ValueError, TypeError):
                    downtime_hours = 0.0

            if downtime_hours is None:
                downtime_hours = 0.0
            else:
                try:
                    downtime_hours = float(downtime_hours)
                except (ValueError, TypeError):
                    downtime_hours = 0.0

            hourly_rate_str = os.environ.get("BASE_HOURLY_RATE_LOSS", "1000.0")
            try:
                hourly_rate = float(hourly_rate_str)
            except (ValueError, TypeError):
                hourly_rate = 1000.0

            total_financial_loss = max(0.0, downtime_hours * hourly_rate)

            result = {
                "incident_id": incident_id or impact_data.get("incident_id"),
                "total_financial_loss": total_financial_loss,
                "estimated_loss_usd": total_financial_loss
            }
            return result

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(str(e))

def incident_financial_impact_evaluator(incident_id_or_data):
    evaluator = IncidentFinancialImpactEvaluator()
    return evaluator.evaluate(incident_id_or_data)