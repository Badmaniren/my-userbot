import os
from skills.telemetry_incident_lifecycle_bridge import TelemetryIncidentLifecycleBridge
from skills.dependency_audit_reporter import DependencyAuditReporter


class AnomalyAuditBridgeException(Exception):
    """Исключение, возникающее при ошибках аудита или жизненного цикла аномалий телеметрии."""
    pass


class AuditBridgeException(AnomalyAuditBridgeException):
    """Псевдоним исключения для совместимости с интеграционными тестами."""
    pass


class TelemetryAnomalyAuditBridge:
    """Мост для связи жизненного цикла инцидентов телеметрии, аудита зависимостей и метрик здоровья."""

    def __init__(self, workspace_dir=None, lifecycle_bridge=None, audit_reporter=None, **kwargs):
        self.workspace_dir = workspace_dir or "/tmp"
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        self.lifecycle_bridge = lifecycle_bridge or TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir, 
            **kwargs
        )
        self.audit_reporter = audit_reporter or DependencyAuditReporter()

    def audit_health_after_incident(self, telemetry_payload, epic_id=None, stream=None):
        try:
            self.lifecycle_bridge.process_lifecycle_event(telemetry_payload)
            
            if hasattr(self.lifecycle_bridge, "verify_and_close_lifecycle"):
                res = self.lifecycle_bridge.verify_and_close_lifecycle()
                lifecycle_closed = bool(res) if res is not None else True
            else:
                lifecycle_closed = True

            if hasattr(self.audit_reporter, 'generate_report'):
                try:
                    audit_report = self.audit_reporter.generate_report(telemetry_payload)
                except TypeError:
                    audit_report = self.audit_reporter.generate_report()
            else:
                audit_report = str(telemetry_payload)

            epic_finalized = False
            if epic_id is not None and stream is not None:
                try:
                    epic_finalized = self.audit_reporter.finalize_epic(epic_id, stream)
                except AttributeError:
                    import io
                    if isinstance(stream, str):
                        stream_obj = io.BytesIO(stream.encode('utf-8'))
                    elif isinstance(stream, bytes):
                        stream_obj = io.BytesIO(stream)
                    else:
                        stream_obj = io.BytesIO(str(stream).encode('utf-8'))
                    epic_finalized = self.audit_reporter.finalize_epic(epic_id, stream_obj)

            incident_id = telemetry_payload.get("incident_id")

            return {
                "lifecycle_closed": lifecycle_closed,
                "audit_report": audit_report,
                "epic_finalized": epic_finalized,
                "incident_id": incident_id
            }
        except AnomalyAuditBridgeException:
            raise
        except Exception as e:
            raise AnomalyAuditBridgeException(f"Failed to audit health after incident: {e}")

    def process_audit_stream(self, stream_io, epic_id=None, export_format=None):
        try:
            self.lifecycle_bridge.process_lifecycle_stream(stream_io)

            if isinstance(stream_io, dict):
                summary_payload = stream_io
            else:
                stream_content = ""
                if hasattr(stream_io, "getvalue"):
                    stream_content = stream_io.getvalue()
                elif hasattr(stream_io, "read"):
                    if hasattr(stream_io, "seek"):
                        try:
                            stream_io.seek(0)
                        except Exception:
                            pass
                    stream_content = stream_io.read()
                    if isinstance(stream_content, bytes):
                        stream_content = stream_content.decode('utf-8', errors='ignore')
                else:
                    stream_content = str(stream_io)

                summary_payload = {
                    "epic_id": epic_id,
                    "stream_data": stream_content,
                    "format": export_format or "json"
                }

            if hasattr(self.audit_reporter, 'export_summary'):
                try:
                    if export_format:
                        summary = self.audit_reporter.export_summary(summary_payload, format=export_format)
                    else:
                        summary = self.audit_reporter.export_summary(summary_payload)
                except TypeError:
                    try:
                        summary = self.audit_reporter.export_summary(stream_io)
                    except TypeError:
                        summary = self.audit_reporter.export_summary()
            else:
                summary = str(summary_payload)

            return summary
        except Exception as e:
            raise AnomalyAuditBridgeException(f"Failed to process audit stream: {e}")

    def generate_epic_health_export(self, payload, output_path):
        try:
            return self.audit_reporter.generate_epic_report(payload, output_path)
        except Exception as e:
            raise AnomalyAuditBridgeException(f"Failed to generate epic health export: {e}")

    def process_anomaly_and_audit(self, telemetry_payload, audit_data):
        try:
            incident_id = telemetry_payload.get("incident_id")
            
            self.lifecycle_bridge.process_lifecycle_event(telemetry_payload)
            
            if hasattr(self.audit_reporter, 'generate_report'):
                try:
                    audit_report = self.audit_reporter.generate_report(audit_data)
                except TypeError:
                    audit_report = self.audit_reporter.generate_report()
            else:
                audit_report = str(audit_data)
            
            return {
                "audit_report": audit_report,
                "lifecycle_status": "PROCESSED",
                "incident_id": incident_id
            }
        except Exception as e:
            raise AuditBridgeException(f"Integration process failed: {e}")
