import json
import uuid
import io
import os

from skills.incident_aggregator import incident_aggregator as default_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator as default_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer as default_trend_analyzer
from skills.system_health_aggregator import system_health_aggregator as default_health_aggregator
from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer
from skills.system_health_aggregator import system_health_aggregator


class IncidentPostMortemReportBuilder:
    def __init__(
        self,
        incident_aggregator=None,
        incident_severity_evaluator=None,
        incident_trend_analyzer=None,
        system_health_telemetry_collector=None
    ):
        self.aggregator = incident_aggregator if incident_aggregator is not None else default_aggregator
        self.evaluator = incident_severity_evaluator if incident_severity_evaluator is not None else default_evaluator
        self.trend_analyzer = incident_trend_analyzer if incident_trend_analyzer is not None else default_trend_analyzer
        self.telemetry_collector = system_health_telemetry_collector if system_health_telemetry_collector is not None else default_health_aggregator

    def build_report(self, incident_id):
        if hasattr(self.aggregator, 'get_incident'):
            incident_data = self.aggregator.get_incident(incident_id)
        elif hasattr(self.aggregator, '__getitem__'):
            incident_data = self.aggregator[incident_id]
        elif isinstance(self.aggregator, dict):
            incident_data = self.aggregator.get(incident_id)
        else:
            incident_data = None

        if incident_data is None:
            raise ValueError(f"Incident with id {incident_id} not found.")

        if hasattr(self.evaluator, 'evaluate'):
            severity_data = self.evaluator.evaluate(incident_data)
        elif callable(self.evaluator):
            severity_data = self.evaluator(incident_data)
        else:
            severity_data = {}

        if hasattr(self.trend_analyzer, 'analyze'):
            trend_data = self.trend_analyzer.analyze(incident_data)
        elif hasattr(self.trend_analyzer, 'analyze_trends'):
            trend_data = self.trend_analyzer.analyze_trends(incident_data)
        elif callable(self.trend_analyzer):
            trend_data = self.trend_analyzer(incident_data)
        else:
            trend_data = {}

        if hasattr(self.telemetry_collector, 'collect'):
            telemetry_data = self.telemetry_collector.collect()
        elif hasattr(self.telemetry_collector, 'collect_and_aggregate'):
            telemetry_data = self.telemetry_collector.collect_and_aggregate()
        elif callable(self.telemetry_collector):
            telemetry_data = self.telemetry_collector()
        else:
            telemetry_data = {}

        return {
            "incident_details": incident_data,
            "severity_assessment": severity_data,
            "trend_analysis": trend_data,
            "system_telemetry": telemetry_data
        }

    def export_report_stream(self, incident_id, stream):
        report = self.build_report(incident_id)
        content = json.dumps(report, ensure_ascii=False, indent=2)
        stream.write(content.encode('utf-8'))
        stream.seek(0)
        return stream


def incident_post_mortem_report_builder(data):
    incident = data.get("incident", {})
    severity = data.get("severity", {})
    trend = data.get("trend", {})
    health = data.get("health", {})

    report_id = str(uuid.uuid4())
    report_content = {
        "report_id": report_id,
        "incident_details": incident,
        "severity_assessment": severity,
        "trend_analysis": trend,
        "system_telemetry": health
    }

    file_path = f"report_{report_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report_content, f, ensure_ascii=False, indent=2)

    report_content["file_path"] = file_path
    return report_content