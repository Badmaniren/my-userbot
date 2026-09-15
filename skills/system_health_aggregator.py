import json
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class SystemHealthAggregator:
    def __init__(self, reporter=None):
        if reporter is None:
            from skills.system_health_reporter import SystemHealthReporter
            self.reporter = SystemHealthReporter(aggregator=self)
        else:
            self.reporter = reporter
        self.dashboard_gen = RecoveryDashboardGenerator()

    def collect_and_aggregate(
        self,
        module_name=None,
        incident_data=None,
        audit_summary=None,
        metrics=None,
        dashboard_format="json",
        incidents_list=None,
        patches_list=None,
        _direct=False,
        **kwargs
    ):
        # Поддержка альтернативных имен аргументов из различных тестов
        if module_name is None:
            module_name = kwargs.get('module', 'default_module')
        if incident_data is None:
            incident_data = kwargs.get('incidents', {})
        if audit_summary is None:
            audit_summary = kwargs.get('audit', {})
        if metrics is None:
            metrics = kwargs.get('system_metrics', {})

        if incidents_list is None:
            if isinstance(incident_data, list):
                incidents_list = incident_data
            elif incident_data is not None:
                incidents_list = [incident_data]
            else:
                incidents_list = []
        
        if _direct:
            report = json.dumps({
                "module": module_name,
                "incident_data": incident_data or {},
                "audit_summary": audit_summary or {},
                "metrics": metrics or {}
            }, ensure_ascii=False)
        else:
            report = self.reporter.generate_health_report(
                module_name,
                incident_data,
                audit_summary,
                metrics
            )
        
        self.dashboard_gen.aggregate_system_health()
        
        dashboard = self.dashboard_gen.generate_dashboard(
            metrics=metrics,
            incidents=incidents_list,
            reports=[report],
            format=dashboard_format
        )
        
        return {
            'report': report,
            'dashboard': dashboard
        }

    def aggregate_and_report(self, *args, **kwargs):
        return self.collect_and_aggregate(*args, **kwargs)

    def process_stream(self, stream, path):
        stream_bytes = stream.read()
        parsed_data = self.dashboard_gen.parse_stream_data(stream_bytes)
        
        if isinstance(parsed_data, (dict, list)):
            payload_to_write = json.dumps(parsed_data)
        else:
            payload_to_write = str(parsed_data) if parsed_data is not None else ""
            
        result = self.dashboard_gen.export_dashboard(payload_to_write, path)
        return result

    def aggregate_system_metrics(self, incidents_list, patches_list):
        total_incidents = len(incidents_list) if isinstance(incidents_list, list) else 0
        total_patches = len(patches_list) if isinstance(patches_list, list) else 0
        return {
            "total_incidents": total_incidents,
            "total_patches": total_patches,
            "incidents": incidents_list,
            "patches": patches_list
        }

    def aggregate_metrics_from_lists(self, incidents_list, patches_list):
        return self.aggregate_system_metrics(incidents_list, patches_list)

    def save_dashboard_file(self, payload, path):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        self.dashboard_gen.export_dashboard_file(payload, path)

    def export_dashboard_file(self, payload, path):
        self.save_dashboard_file(payload, path)

    def save_health_report(self, health_report, path):
        if isinstance(health_report, (dict, list)):
            health_report = json.dumps(health_report)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(health_report))
            return True
        except Exception:
            return False

    def parse_reporter_stream(self, stream):
        if hasattr(stream, "read"):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            try:
                return json.loads(content)
            except Exception:
                return content
        return None