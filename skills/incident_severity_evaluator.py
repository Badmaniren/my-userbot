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

    def evaluate(self, module_name, exception=None, traceback_str=None, incident_id=None):
        if isinstance(module_name, dict):
            payload_dict = dict(module_name)
            payload_dict.pop("severity_assessment", None)
            inc_id = payload_dict.get("incident_id") or incident_id
            severity = payload_dict.get("severity")
            if not severity:
                severity = self.calculate_severity_score(payload_dict)

            payload = payload_dict.get("payload")
            if payload is None:
                if hasattr(self.template_engine, "generate_notification_payload"):
                    try:
                        payload = self.template_engine.generate_notification_payload(
                            severity, inc_id, payload_dict
                        )
                    except Exception:
                        payload = payload_dict
                else:
                    payload = payload_dict

            return {
                "incident_id": inc_id,
                "severity": severity,
                "payload": payload,
                "aggregated_data": payload_dict,
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

    def evaluate_stream(self, module_name: str, stream_data=None):
        if stream_data is None and not isinstance(module_name, str):
            stream_data = module_name
            module_name = "default_module"

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

    def evaluate_and_notify(self, module_name, exception=None, traceback_str=None, incident_id=None):
        eval_res = self.evaluate(module_name, exception, traceback_str, incident_id)
        inc_id = eval_res.get("incident_id")
        severity = eval_res.get("severity")
        agg_data = eval_res.get("aggregated_data", {})
        
        if hasattr(self.template_engine, "generate_notification_payload"):
            try:
                notification = self.template_engine.generate_notification_payload(
                    severity, inc_id, agg_data
                )
            except Exception:
                notification = agg_data
        else:
            notification = agg_data
        
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


def evaluate_incident_severity(module_name, exception=None, traceback_str=None, incident_id=None):
    evaluator = IncidentSeverityEvaluator()
    return evaluator.evaluate(module_name, exception, traceback_str, incident_id)
