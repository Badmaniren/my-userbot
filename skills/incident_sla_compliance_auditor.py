import json

try:
    import requests
except (ImportError, ModuleNotFoundError):
    requests = None

try:
    from skills.incident_aggregator import incident_aggregator
except ImportError:
    try:
        from skills.incident_aggregator import aggregate_incidents as incident_aggregator
    except ImportError:
        try:
            from skills.incident_aggregator import IncidentAggregator as incident_aggregator
        except ImportError:
            incident_aggregator = None

try:
    from skills.incident_sla_tracker import incident_sla_tracker
except ImportError:
    incident_sla_tracker = None


class IncidentSlaComplianceAuditor:
    """
    Analyzes historical incident data against SLA targets to generate compliance reports
    and identify systemic gaps in recovery performance.
    """

    def generate_compliance_report(self, filepath: str) -> dict:
        with open(filepath, 'r') as f:
            data = json.load(f)

        total = data.get("total_incidents", 0)
        breached = data.get("breached_incidents", 0)

        compliance_pct = self._calculate_compliance_percentage(total, breached)

        # Identify gaps: if recovery time > 60 mins, flag as potential systemic issue
        recovery_times = data.get("recovery_times_minutes", [])
        gaps = [t for t in recovery_times if t > 60]

        return {
            "client_id": data.get("client_id"),
            "compliance_percentage": compliance_pct,
            "systemic_gaps_identified": gaps
        }

    def audit_compliance(self, data=None, **kwargs) -> dict:
        if data is None:
            data = kwargs
        if isinstance(data, str):
            return self.generate_compliance_report(data)
        if isinstance(data, dict):
            total = data.get("total_incidents", 0)
            breached = data.get("breached_incidents", 0)
            compliance_pct = self._calculate_compliance_percentage(total, breached)
            recovery_times = data.get("recovery_times_minutes", [])
            gaps = [t for t in recovery_times if t > 60]
            return {
                "client_id": data.get("client_id"),
                "compliance_percentage": compliance_pct,
                "systemic_gaps_identified": gaps
            }
        return {"compliance_percentage": 100.0, "systemic_gaps_identified": []}

    def identify_systemic_gaps(self, filepath: str) -> list:
        with open(filepath, 'r') as f:
            data = json.load(f)

        incidents = data.get("incidents", [])
        # Logic: identify incidents that took longer than 120 minutes as systemic gaps
        return [inc for inc in incidents if inc.get("duration", 0) > 120]

    def audit_recovery_performance_from_api(self, endpoint: str, token: str) -> dict:
        if requests is None:
            return {"audited_incidents": {}}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(endpoint, headers=headers)
        data = response.json()

        # Return summary of audited incidents
        return {"audited_incidents": data}

    def _calculate_compliance_percentage(self, total: int, breached: int) -> float:
        if total == 0:
            return 100.0
        return round(((total - breached) / total) * 100, 2)


IncidentSLAComplianceAuditor = IncidentSlaComplianceAuditor


def incident_sla_compliance_auditor(tracked_sla: dict = None, **kwargs) -> dict:
    """
    Integration helper function to process tracked SLA data.
    """
    if tracked_sla is None:
        tracked_sla = kwargs
    elif not isinstance(tracked_sla, dict):
        tracked_sla = {"incident_id": tracked_sla, **kwargs}
    res_time = tracked_sla.get("resolution_time_minutes", 0)
    target = tracked_sla.get("sla_target_minutes", 0)

    status = "COMPLIANT" if res_time <= target else "BREACH"

    return {
        "audited_incident_id": tracked_sla.get("incident_id"),
        "compliance_status": status
    }
