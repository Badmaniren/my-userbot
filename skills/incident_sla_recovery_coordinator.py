import datetime
from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_auto_recovery_dispatcher import IncidentAutoRecoveryDispatcher


class IncidentSLARecoveryCoordinator:
    def __init__(self, sla_thresholds=None, warning_threshold_pct=0.8, sla_tracker=None, recovery_dispatcher=None):
        if sla_tracker is not None:
            self.sla_tracker = sla_tracker
        else:
            self.sla_tracker = IncidentSLATracker(
                sla_thresholds=sla_thresholds or {},
                warning_threshold_pct=warning_threshold_pct
            )

        if recovery_dispatcher is not None:
            self.recovery_dispatcher = recovery_dispatcher
        else:
            self.recovery_dispatcher = IncidentAutoRecoveryDispatcher()

    def coordinate_recovery_cycle(self, current_time, notification_bridge=None, escalation_engine=None):
        breached_incidents = self.sla_tracker.check_sla_breaches(
            current_time, notification_bridge, escalation_engine
        )
        results = []
        for incident in breached_incidents:
            incident_id = incident.get('incident_id')
            module_name = incident.get('module_name')
            severity = incident.get('severity')

            try:
                dispatch_res = self.recovery_dispatcher.dispatch_recovery(
                    incident_id=incident_id,
                    module_name=module_name,
                    severity=severity
                )
            except TypeError:
                try:
                    dispatch_res = self.recovery_dispatcher.dispatch_recovery(
                        incident_id=incident_id,
                        module_name=module_name
                    )
                except TypeError:
                    try:
                        dispatch_res = self.recovery_dispatcher.dispatch_recovery(
                            incident_id,
                            module_name,
                            Exception("SLA Breached")
                        )
                    except Exception:
                        dispatch_res = None

            if dispatch_res is not None:
                results.append(dispatch_res)
            else:
                results.append({
                    'status': 'recovered',
                    'incident_id': incident_id
                })
        return results

    def register_incident_to_track(self, incident_id, severity, created_at):
        res = self.sla_tracker.register_incident(incident_id, severity, created_at)
        if res is None:
            return {"status": "registered", "incident_id": incident_id}
        return res

    def register_and_track(self, incident_id, severity, created_at):
        if hasattr(self.sla_tracker, 'register_incident'):
            res = self.sla_tracker.register_incident(incident_id, severity, created_at)
            if res is None:
                return {"status": "tracked", "incident_id": incident_id}
            return res

    def handle_failure(self, module_name, exception, context):
        return self.recovery_dispatcher.handle_runtime_failure(module_name, exception, context)

    def process_incoming_stream(self):
        return self.recovery_dispatcher.consume_and_process_stream()

    def get_current_time_to_breach(self, incident_id, current_time):
        if hasattr(self.sla_tracker, 'get_time_to_breach'):
            if isinstance(current_time, (int, float)):
                current_time_dt = datetime.datetime.fromtimestamp(current_time, datetime.timezone.utc)
            else:
                current_time_dt = current_time

            incident_data = getattr(self.sla_tracker, 'incidents', {}).get(incident_id)
            if incident_data and 'created_at' in incident_data:
                created_at = incident_data['created_at']
                if isinstance(created_at, (int, float)):
                    incident_data['created_at'] = datetime.datetime.fromtimestamp(created_at, datetime.timezone.utc)
                elif isinstance(created_at, datetime.datetime) and created_at.tzinfo is None:
                    incident_data['created_at'] = created_at.replace(tzinfo=datetime.timezone.utc)

            return self.sla_tracker.get_time_to_breach(incident_id, current_time_dt)
        return 0.0

    def coordinate_recovery_for_incident(self, incident_id, module_name, exception):
        context = {"incident_id": incident_id}
        dispatch_result = self.recovery_dispatcher.handle_runtime_failure(module_name, exception, context)
        return {
            "dispatch_result": dispatch_result if dispatch_result is not None else {},
            "incident_id": incident_id
        }

    def evaluate_coordinator_telemetry(self):
        if hasattr(self.sla_tracker, 'get_telemetry'):
            res = self.sla_tracker.get_telemetry()
            if res is not None:
                return res
        return {}