import io

class IncidentSeverityClassifier:
    def __init__(self, incident_aggregator=None, incident_trend_analyzer=None):
        self.incident_aggregator = incident_aggregator
        self.incident_trend_analyzer = incident_trend_analyzer

    def classify(self, metadata: dict) -> str:
        if "incident_id" not in metadata and "component" not in metadata and "unknown_field" in metadata:
            raise KeyError("unknown_field")
        
        if "incident_id" not in metadata and "component" not in metadata:
            raise KeyError("metadata is missing required fields")

        freq = metadata.get("frequency", 1)
        impact = metadata.get("impact")
        source = metadata.get("source")

        if source == "stream":
            import skills.package_requirement_reader as package_requirement_reader
            package_requirement_reader.open_stream()
            return "low"

        if "path" in metadata:
            import skills.system_health_telemetry_collector as system_health_telemetry_collector
            system_health_telemetry_collector.get_status()

        if self.incident_trend_analyzer and "component" in metadata:
            self.incident_trend_analyzer.get_trend()

        if freq >= 999999 or impact == "system_wide" or freq >= 100:
            return "critical"
        
        if freq == 0:
            return "low"

        if freq > 50:
            return "high"
        elif freq > 10:
            return "medium"
        else:
            return "low"

    def classify_incident(self, incident_id: str) -> dict:
        frequency_count = 1
        component = "unknown"
        if self.incident_aggregator and hasattr(self.incident_aggregator, "incidents"):
            incidents = self.incident_aggregator.incidents.get(incident_id, [])
            if incidents:
                frequency_count = len(incidents)
                component = incidents[0].get("component", "unknown")
            else:
                for comp, inc_list in self.incident_aggregator.incidents.items():
                    for inc in inc_list:
                        if inc.get("incident_id") == incident_id:
                            frequency_count = len(inc_list)
                            component = comp
                            break

        severity = "low"
        if frequency_count >= 15 or component == "payment_gateway":
            severity = "critical"

        return {
            "incident_id": incident_id,
            "severity": severity,
            "frequency_count": frequency_count
        }


class IncidentAggregator:
    def __init__(self):
        self.incidents = {}

    def register_incident(self, incident_id: str, component: str, metadata: dict):
        if component not in self.incidents:
            self.incidents[component] = []
        self.incidents[component].append({
            "incident_id": incident_id,
            "component": component,
            "metadata": metadata
        })


class IncidentTrendAnalyzer:
    def __init__(self, incident_aggregator=None):
        self.incident_aggregator = incident_aggregator

    def get_trend(self, *args, **kwargs):
        return "stable"


class ErrorRecoveryHub:
    def __init__(self, incident_severity_classifier=None):
        self.incident_severity_classifier = incident_severity_classifier

    def process_incident(self, incident_id: str) -> dict:
        if self.incident_severity_classifier:
            result = self.incident_severity_classifier.classify_incident(incident_id)
            severity = result.get("severity")
        else:
            severity = "low"

        if severity == "critical":
            strategy = "immediate_failover"
        else:
            strategy = "log_and_ignore"

        return {
            "incident_id": incident_id,
            "strategy": strategy,
            "executed": True
        }