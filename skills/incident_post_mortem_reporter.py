import json
import uuid
import datetime
from skills.incident_aggregator import IncidentAggregator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer

class IncidentPostMortemReporter:
    def __init__(self, incident_aggregator=None, incident_trend_analyzer=None):
        self.incident_aggregator = incident_aggregator if incident_aggregator is not None else IncidentAggregator()
        self.trend_analyzer = incident_trend_analyzer if incident_trend_analyzer is not None else IncidentTrendAnalyzer()

    def generate(self, incident_id):
        if hasattr(self.incident_aggregator, "get_aggregated_incident"):
            aggregated_data = self.incident_aggregator.get_aggregated_incident(incident_id)
        elif hasattr(self.incident_aggregator, "get_incident"):
            aggregated_data = self.incident_aggregator.get_incident(incident_id)
        elif hasattr(self.incident_aggregator, "get_incident_details"):
            aggregated_data = self.incident_aggregator.get_incident_details(incident_id)
        else:
            aggregated_data = {"id": incident_id}

        if aggregated_data is None:
            aggregated_data = {"id": incident_id}

        if hasattr(self.trend_analyzer, "analyze_trend"):
            trend_data = self.trend_analyzer.analyze_trend(aggregated_data)
        elif hasattr(self.trend_analyzer, "analyze"):
            trend_data = self.trend_analyzer.analyze(aggregated_data)
        elif hasattr(self.trend_analyzer, "analyze_trends"):
            trend_data = self.trend_analyzer.analyze_trends(aggregated_data)
        else:
            trend_data = {}

        if trend_data is None:
            trend_data = {}

        report = {
            "incident_id": aggregated_data.get("id", incident_id) if isinstance(aggregated_data, dict) else incident_id,
            "severity": aggregated_data.get("severity") if isinstance(aggregated_data, dict) else None,
            "summary": aggregated_data.get("summary") if isinstance(aggregated_data, dict) else None,
            "trend_score": trend_data.get("recurrence_score") if isinstance(trend_data, dict) else None,
            "generated_at": datetime.datetime.utcnow().isoformat()
        }
        return report

    def export_to_stream(self, incident_id, stream):
        report = self.generate(incident_id)
        content = json.dumps(report, ensure_ascii=False)
        encoded_content = content.encode("utf-8")
        stream.write(encoded_content)
        return len(encoded_content)


def generate_incident_post_mortem(system_id, aggregated_data, trend_analysis, output_path):
    report_id = str(uuid.uuid4())
    result = {
        "report_id": report_id,
        "system_id": system_id,
        "aggregated_data": aggregated_data,
        "trend_analysis": trend_analysis,
        "generated_at": datetime.datetime.utcnow().isoformat()
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


incident_post_mortem_reporter = IncidentPostMortemReporter
