import io
from skills.incident_aggregator import incident_aggregator
from skills.auto_patch_pipeline import auto_patch_pipeline


class EscalationConfigurationError(Exception):
    pass


class ExternalAggregatorConnectionError(Exception):
    pass


class IncidentAutoEscalationEngine:
    def __init__(self, severity_evaluator=True, aggregator=None):
        if severity_evaluator is None:
            raise EscalationConfigurationError("severity_evaluator cannot be None")
        self.severity_evaluator = severity_evaluator
        self.aggregator = aggregator or incident_aggregator

    def escalate(self, incident_id, system_name="default_system", severity="CRITICAL"):
        try:
            return self.aggregator(incident_id, system_name, severity)
        except Exception as e:
            if isinstance(e, (EscalationConfigurationError, ExternalAggregatorConnectionError)):
                raise
            raise ExternalAggregatorConnectionError(str(e)) from e


def incident_auto_escalation_engine(*args, **kwargs):
    if len(args) >= 3 and isinstance(args[0], str) and isinstance(args[1], str) and isinstance(args[2], str):
        return escalate_incident(args[0], args[1], args[2])
    elif len(args) == 2 and hasattr(args[0], "read"):
        return evaluate_and_escalate(args[0], args[1])
    return IncidentAutoEscalationEngine(*args, **kwargs)


def escalate_incident(incident_id, system_name, severity):
    return incident_aggregator(incident_id, system_name, severity)


def evaluate_and_escalate(stream_data, threshold):
    content = stream_data.read().decode('utf-8')
    parts = content.strip().split(':')

    if len(parts) >= 3:
        incident_id = parts[1]
        metric_value = int(parts[2])

        if metric_value >= threshold:
            system_name = "default_system"
            severity = "CRITICAL"
            return incident_aggregator(incident_id, system_name, severity)

    return None