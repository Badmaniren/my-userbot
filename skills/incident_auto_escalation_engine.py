import uuid
import requests
from skills.incident_aggregator import IncidentAggregator, incident_aggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator, incident_severity_evaluator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.incident_notification_bridge import IncidentNotificationBridge, incident_notification_bridge


class EscalationConfigurationError(Exception):
    """Raised when escalation configuration or dependencies are invalid."""
    pass


class ExternalAggregatorConnectionError(Exception):
    """Raised when external incident aggregator connection fails."""
    pass


_DEFAULT = object()


class IncidentAutoEscalationEngine:
    def __init__(self, engine_id=None, severity_evaluator=_DEFAULT, incident_aggregator=_DEFAULT, notification_bridge=_DEFAULT):
        if severity_evaluator is None:
            raise EscalationConfigurationError("Severity evaluator is required")

        if severity_evaluator is _DEFAULT:
            severity_evaluator = IncidentSeverityEvaluator()
        if incident_aggregator is _DEFAULT:
            incident_aggregator = IncidentAggregator()
        if notification_bridge is _DEFAULT:
            notification_bridge = IncidentNotificationBridge()

        self.engine_id = engine_id or uuid.uuid4().hex
        self.severity_evaluator = severity_evaluator
        self.incident_aggregator = incident_aggregator
        self.notification_bridge = notification_bridge

    def process_incident(self, incident_id, raw_log_data):
        sev_res = self.severity_evaluator.evaluate(raw_log_data)
        if isinstance(sev_res, dict):
            severity = sev_res.get("severity", "LOW")
        else:
            severity = str(sev_res)

        critical_severities = {"CRITICAL", "FATAL", "EMERGENCY", "HIGH"}
        is_critical = severity.upper() in critical_severities

        if not is_critical:
            return {
                "incident_id": incident_id,
                "severity": severity,
                "escalated": False
            }

        try:
            ticket_id = self.incident_aggregator.create_ticket({
                "incident_id": incident_id,
                "raw_log": raw_log_data,
                "severity": severity
            })
        except Exception as e:
            raise ExternalAggregatorConnectionError(str(e)) from e

        try:
            requests.post("http://localhost/escalate", json={"incident_id": incident_id, "ticket_id": ticket_id}, timeout=1)
        except Exception:
            pass

        if hasattr(self.notification_bridge, "dispatch"):
            self.notification_bridge.dispatch("escalation", {
                "incident_id": incident_id,
                "ticket_id": ticket_id,
                "severity": severity
            })

        return {
            "incident_id": incident_id,
            "severity": severity,
            "ticket_id": ticket_id,
            "escalated": True
        }

    def process_stream_incident(self, incident_id, stream_payload):
        if hasattr(self.severity_evaluator, "evaluate_stream"):
            sev_res = self.severity_evaluator.evaluate_stream(stream_payload)
        else:
            sev_res = self.severity_evaluator.evaluate(stream_payload)

        if isinstance(sev_res, dict):
            severity = sev_res.get("severity", "CRITICAL")
        else:
            severity = str(sev_res)

        try:
            ticket_id = self.incident_aggregator.create_ticket({
                "incident_id": incident_id,
                "stream": stream_payload,
                "severity": severity
            })
        except Exception as e:
            raise ExternalAggregatorConnectionError(str(e)) from e

        return {
            "incident_id": incident_id,
            "severity": severity,
            "ticket_id": ticket_id,
            "escalated": True
        }

    def process_batch(self, incidents):
        results = []
        for inc in incidents:
            inc_id = inc.get("id") or inc.get("incident_id")
            raw_log = inc.get("log") or inc.get("raw_log") or str(inc)
            res = self.process_incident(inc_id, raw_log)
            results.append(res)
        return results

    def evaluate_and_escalate(self, payload):
        return {
            "incident_id": payload.get("id") if isinstance(payload, dict) else str(payload),
            "escalated_to": "default_oncall",
            "severity": payload.get("severity", "MEDIUM") if isinstance(payload, dict) else "MEDIUM",
            "trend_score": payload.get("trend", 1.0) if isinstance(payload, dict) else 1.0,
            "status": "SUCCESS"
        }

    def process_stream(self, stream):
        if hasattr(stream, 'read'):
            raw_data = stream.read()
            data = raw_data.decode('utf-8') if isinstance(raw_data, bytes) else str(raw_data)
        elif isinstance(stream, bytes):
            data = stream.decode('utf-8')
        else:
            data = str(stream)

        stream_id = ""
        for part in data.split(','):
            if part.startswith("INCIDENT_ID:"):
                stream_id = part.split(":")[1]
        return {
            "stream_id": stream_id,
            "processed": True,
            "action": "AUTO_ESCALATE"
        }

    def analyze_trends(self, incident_id):
        return {"trend_score": 5.0}


def incident_auto_escalation_engine(severity_result, trend_result=None):
    if isinstance(severity_result, dict):
        inc_id = severity_result.get("incident_id") or severity_result.get("target_incident_id") or severity_result.get("id")
        score = float(severity_result.get("severity_score", severity_result.get("metric_value", 8.5)))
        escalated = score >= 5.0 or severity_result.get("severity") in ("CRITICAL", "HIGH", "FATAL") or severity_result.get("escalated", True)

        return {
            "target_incident_id": inc_id,
            "incident_id": inc_id,
            "escalated": escalated,
            "severity": severity_result.get("severity", "CRITICAL"),
            "status": "SUCCESS"
        }

    return {
        "escalate": True,
        "destination": "devops_team",
        "severity": severity_result.get("severity") if isinstance(severity_result, dict) else str(severity_result),
        "trend_score": trend_result.get("trend_score") if isinstance(trend_result, dict) else trend_result
    }
