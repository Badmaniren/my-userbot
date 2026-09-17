from typing import Any
from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine


class IncidentSeverityEvaluator:
    def __init__(self, aggregator=None, template_engine=None):
        self.aggregator = aggregator if aggregator is not None else IncidentAggregator()
        self.template_engine = template_engine if template_engine is not None else NotificationTemplateEngine()

    def calculate_severity_score(self, data: dict) -> str:
        count = data.get("count", 0)
        is_fatal = data.get("is_fatal", False)
        
        if count >= 50 or is_fatal:
            return "CRITICAL"
        elif count >= 26:
            return "HIGH"
        elif count >= 6:
            return "MEDIUM"
        else:
            return "LOW"

    def evaluate(self, module_name: Any = None, exception: Exception = None, traceback_str: str = None, incident_id: str = None):
        if isinstance(module_name, dict):
            raw_dict = dict(module_name)
            raw_dict.pop("severity_assessment", None)
            inc_id = raw_dict.get("incident_id") or raw_dict.get("id") or incident_id or "INC-UNKNOWN"
            metrics = raw_dict.get("metrics") or raw_dict
            count = metrics.get("affected_users") or metrics.get("count", 1)
            error_rate = metrics.get("error_rate", 0)
            if error_rate > 0.5 or count >= 50 or metrics.get("is_fatal"):
                severity = "CRITICAL"
            elif error_rate > 0.2 or count >= 26:
                severity = "HIGH"
            elif error_rate > 0.05 or count >= 6:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            return {
                "incident_id": inc_id,
                "severity": severity,
                "payload": raw_dict,
                "aggregated_data": raw_dict,
            }

        agg_result = self.aggregator.process_and_aggregate(
            module_name, exception, traceback_str, incident_id
        )
        
        severity = self.calculate_severity_score(agg_result)
        inc_id = agg_result.get("incident_id") or incident_id
        
        payload = self.template_engine.generate_notification_payload(
            severity, inc_id, agg_result
        )
        
        return {
            "incident_id": inc_id,
            "severity": severity,
            "payload": payload,
            "aggregated_data": agg_result,
        }

    def evaluate_stream(self, module_name: str, stream_data):
        parsed = self.template_engine.parse_stream_data(stream_data)
        inc_id = parsed.get("parsed_id") or parsed.get("incident_id")
        freq = parsed.get("frequency", parsed.get("count", 1))
        
        severity = self.calculate_severity_score({"count": freq})
        payload = self.template_engine.generate_notification_payload(
            severity, inc_id, parsed
        )
        
        return {
            "incident_id": inc_id,
            "severity": severity,
            "payload": payload,
        }

    def evaluate_and_notify(self, module_name: str, exception: Exception, traceback_str: str, incident_id: str = None):
        eval_res = self.evaluate(module_name, exception, traceback_str, incident_id)
        inc_id = eval_res.get("incident_id")
        severity = eval_res.get("severity")
        agg_data = eval_res.get("aggregated_data", {})
        
        notification = self.template_engine.generate_notification_payload(
            severity, inc_id, agg_data
        )
        
        return {
            "incident_id": inc_id,
            "severity": severity,
            "notification": notification,
            "payload": eval_res.get("payload"),
            "aggregated_data": agg_data,
        }

    def export_incident_report(self, template_name: str, context: dict, output_path: str, format_type: str = "html"):
        self.template_engine.render_template(template_name, context, format_type)
        return self.template_engine.export_notification_file(context, output_path)


def evaluate_incident_severity(module_name: Any = None, exception: Exception = None, traceback_str: str = None, incident_id: str = None):
    evaluator = IncidentSeverityEvaluator()
    return evaluator.evaluate(module_name, exception, traceback_str, incident_id)