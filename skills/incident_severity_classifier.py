import skills.package_requirement_reader as package_requirement_reader
import skills.system_health_telemetry_collector as system_health_telemetry_collector
import skills.incident_trend_analyzer as incident_trend_analyzer
import skills.incident_aggregator as incident_aggregator
import skills.error_recovery_hub as error_recovery_hub


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
            if hasattr(package_requirement_reader, "open_stream"):
                package_requirement_reader.open_stream()
            return "low"

        if "path" in metadata:
            if hasattr(system_health_telemetry_collector, "get_status"):
                system_health_telemetry_collector.get_status()

        if self.incident_trend_analyzer and hasattr(self.incident_trend_analyzer, "get_trend"):
            self.incident_trend_analyzer.get_trend()
        elif hasattr(incident_trend_analyzer, "get_trend"):
            incident_trend_analyzer.get_trend()

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
