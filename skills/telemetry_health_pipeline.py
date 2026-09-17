import json
from skills.telemetry_streamer import TelemetryStreamer
from skills.telemetry_processor import TelemetryProcessor
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class PipelineCompositionError(Exception):
    """Исключение, возникающее при ошибках композиции пайплайна телеметрии."""
    pass

class TelemetryHealthPipeline:
    def __init__(self, stream_id: str, endpoint: str, buffer_size: int):
        self.streamer = TelemetryStreamer(stream_id=stream_id, endpoint=endpoint, buffer_size=buffer_size)
        self.processor = TelemetryProcessor()
        self.collector = SystemHealthTelemetryCollector()

    def run_pipeline_cycle(
        self,
        source_path: str,
        module_name: str,
        incident_data: dict,
        audit_summary,
        metrics: dict,
        dashboard_format: str,
        incidents_list: list,
        patches_list: list,
        report_path: str,
        dashboard_path: str
    ):
        raw_packet = self.streamer.read_from_source(source_path)

        packet_data = None
        if isinstance(raw_packet, bytes):
            try:
                decoded = raw_packet.decode('utf-8')
                try:
                    packet_data = json.loads(decoded)
                except Exception:
                    pass
                raw_packet = decoded
            except UnicodeDecodeError:
                pass
        elif isinstance(raw_packet, str):
            try:
                packet_data = json.loads(raw_packet)
            except Exception:
                pass
        elif isinstance(raw_packet, dict):
            packet_data = raw_packet

        processed_packet = self.processor.process_packet(raw_packet)
        if isinstance(processed_packet, dict):
            if packet_data is None:
                packet_data = processed_packet
            else:
                packet_data.update(processed_packet)

        if isinstance(packet_data, dict) and isinstance(incident_data, dict):
            telemetry_keys = {"device_id", "device_uuid", "cpu_load", "status", "sensor_id", "packet_id", "metric_name"}
            extracted = {k: v for k, v in packet_data.items() if k in telemetry_keys}
            if extracted:
                incident_data = {**incident_data, **extracted}

        result = self.collector.collect_and_process_telemetry(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=report_path,
            dashboard_path=dashboard_path
        )
        return result

    def stream_and_process(self, stream_obj, path: str):
        return self.collector.process_telemetry_stream(stream_obj, path)

    def export_pipeline_report(self, payload: dict, path: str):
        self.collector.export_comprehensive_report(payload, path)

def run_telemetry_health_pipeline(
    source_path: str,
    report_path: str,
    module_name: str,
    incident_data: dict,
    audit_summary,
    metrics: dict,
    dashboard_format: str,
    incidents_list: list,
    patches_list: list,
    stream_id: str = "default_stream",
    endpoint: str = "http://localhost:8080",
    buffer_size: int = 4096,
    dashboard_path: str = None
):
    pipeline = TelemetryHealthPipeline(
        stream_id=stream_id,
        endpoint=endpoint,
        buffer_size=buffer_size
    )

    if dashboard_path is None:
        dashboard_path = report_path + ".dash"

    return pipeline.run_pipeline_cycle(
        source_path=source_path,
        module_name=module_name,
        incident_data=incident_data,
        audit_summary=audit_summary,
        metrics=metrics,
        dashboard_format=dashboard_format,
        incidents_list=incidents_list,
        patches_list=patches_list,
        report_path=report_path,
        dashboard_path=dashboard_path
    )