from skills.incident_aggregator import IncidentAggregator
from skills.notification_template_engine import NotificationTemplateEngine


class IncidentSeverityEvaluator:
    def __init__(self, aggregator=None, template_engine=None, escalation_engine=None):
        self.aggregator = aggregator if aggregator is not None else IncidentAggregator()
        self.template_engine = template_engine if template_engine is not None else NotificationTemplateEngine()
        self._escalation_engine = escalation_engine

    @property
    def escalation_engine(self):
        if self._escalation_engine is None:
            from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
            self._escalation_engine = IncidentAutoEscalationEngine()
        return self._escalation_engine

    @escalation_engine.setter
    def escalation_engine(self, value):
        self._escalation_engine = value

    def calculate_severity_score(self, data: dict) -> str:
        count = data.get("count", 0) if isinstance(data, dict) else 0
        is_fatal = data.get("is_fatal", False) if isinstance(data, dict) else False
        
        if count >= 50 or is_fatal:
            return "CRITICAL"
        elif count >= 26:
            return "HIGH"
        elif count >= 6:
            return "MEDIUM"
        else:
            return "LOW"

    def evaluate(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], dict):
            payload = dict(args[0])
            payload.pop("severity_assessment", None)
            inc_id = payload.get("incident_id") or payload.get("id")
            count = payload.get("count", 1)
            is_fatal = payload.get("is_fatal", False)
            severity = self.calculate_severity_score({"count": count, "is_fatal": is_fatal})
            return {
                "incident_id": inc_id,
                "severity": severity,
                "payload": payload,
                "aggregated_data": payload,
            }
        elif "data" in kwargs and isinstance(kwargs["data"], dict):
            payload = dict(kwargs.pop("data"))
            payload.pop("severity_assessment", None)
            inc_id = payload.get("incident_id") or payload.get("id")
            count = payload.get("count", 1)
            is_fatal = payload.get("is_fatal", False)
            severity = self.calculate_severity_score({"count": count, "is_fatal": is_fatal})
            return {
                "incident_id": inc_id,
                "severity": severity,
                "payload": payload,
                "aggregated_data": payload,
            }
        elif len(args) == 1 and isinstance(args[0], Exception):
            exc = args[0]
            severity = "HIGH" if "critical" in str(exc).lower() or "fatal" in str(exc).lower() else "MEDIUM"
            return {
                "incident_id": None,
                "severity": severity,
                "payload": {"error": str(exc)},
            }
        elif len(args) == 2 and isinstance(args[0], Exception):
            exc, tb_str = args[0], args[1]
            severity = "CRITICAL" if "critical" in str(exc).lower() or "fatal" in str(exc).lower() else "HIGH"
            return {
                "incident_id": None,
                "severity": severity,
                "payload": {"error": str(exc), "traceback": tb_str},
            }

        module_name = args[0] if len(args) > 0 else kwargs.get("module_name")
        exception = args[1] if len(args) > 1 else kwargs.get("exception")
        traceback_str = args[2] if len(args) > 2 else kwargs.get("traceback_str")
        incident_id = args[3] if len(args) > 3 else kwargs.get("incident_id")

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
        if parsed is None:
            parsed = {} if not isinstance(stream_data, dict) else stream_data

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


SeverityEvaluator = IncidentSeverityEvaluator
incident_severity_evaluator = IncidentSeverityEvaluator()


def evaluate(*args, **kwargs):
    if len(args) == 1 and isinstance(args[0], dict):
        d = dict(args[0])
        d.pop("severity_assessment", None)
        count = d.get("count", 1)
        is_fatal = d.get("is_fatal", False)
        evaluator = IncidentSeverityEvaluator()
        return evaluator.calculate_severity_score({"count": count, "is_fatal": is_fatal})
    elif "data" in kwargs and isinstance(kwargs["data"], dict):
        d = dict(kwargs["data"])
        d.pop("severity_assessment", None)
        count = d.get("count", 1)
        is_fatal = d.get("is_fatal", False)
        evaluator = IncidentSeverityEvaluator()
        return evaluator.calculate_severity_score({"count": count, "is_fatal": is_fatal})
    elif len(args) == 1 and isinstance(args[0], str):
        evaluator = IncidentSeverityEvaluator()
        return evaluator.evaluate({"incident_id": args[0]})
    evaluator = IncidentSeverityEvaluator()
    return evaluator.evaluate(*args, **kwargs)


def evaluate_incident_severity(module_name: str = None, exception: Exception = None, traceback_str: str = None, incident_id: str = None, *args, **kwargs):
    evaluator = IncidentSeverityEvaluator()
    if module_name is not None or exception is not None or traceback_str is not None or incident_id is not None:
        return evaluator.evaluate(module_name, exception, traceback_str, incident_id, *args, **kwargs)
    return evaluate(*args, **kwargs)