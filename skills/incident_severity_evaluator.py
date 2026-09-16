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

    def evaluate(self, module_name=None, exception=None, traceback_str=None, incident_id=None, severity_data=None, **kwargs):
        if isinstance(module_name, dict) or isinstance(severity_data, dict):
            data = module_name if isinstance(module_name, dict) else severity_data
            payload = dict(data)
            payload.pop("severity_assessment", None)
            inc_id = payload.get("incident_id") or payload.get("id") or incident_id
            severity = payload.get("severity") or self.calculate_severity_score(payload)
            return {
                "incident_id": inc_id,
                "severity": severity,
                "payload": payload,
                "aggregated_data": payload,
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


def evaluate_incident_severity(module_name: str, exception: Exception, traceback_str: str, incident_id: str = None):
    evaluator = IncidentSeverityEvaluator()
    return evaluator.evaluate(module_name, exception, traceback_str, incident_id)


def incident_severity_evaluator(module_name=None, exception=None, traceback_str=None, incident_id=None, severity_data=None, **kwargs):
    evaluator = IncidentSeverityEvaluator(
        aggregator=kwargs.get("aggregator"),
        template_engine=kwargs.get("template_engine")
    )
    if module_name is None and exception is None and severity_data is None and not kwargs:
        return evaluator
    return evaluator.evaluate(
        module_name=module_name,
        exception=exception,
        traceback_str=traceback_str,
        incident_id=incident_id,
        severity_data=severity_data,
        **kwargs
    )


incident_severity_evaluator.evaluate = lambda *args, **kwargs: IncidentSeverityEvaluator().evaluate(*args, **kwargs)
incident_severity_evaluator.calculate_severity_score = lambda *args, **kwargs: IncidentSeverityEvaluator().calculate_severity_score(*args, **kwargs)
