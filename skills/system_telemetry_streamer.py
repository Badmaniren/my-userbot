import time
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector as BaseCollector, collect_telemetry_metrics
from skills.system_health_aggregator import aggregate_system_health


class SystemHealthTelemetryCollector(BaseCollector):
    def collect(self, *args, **kwargs):
        return super().collect(*args, **kwargs)


class SystemHealthMonitoringGateway:
    def ingest(self, data, *args, **kwargs):
        return True


class SystemTelemetryStreamer:
    def stream_telemetry(self, stream_id=None, *args, **kwargs):
        if "stream_stream_id" in kwargs:
            stream_id = kwargs.pop("stream_stream_id")

        collector = SystemHealthTelemetryCollector()
        source = collector.collect(stream_id, *args, **kwargs)

        if source is None:
            return None

        raw_data = source.read()

        gateway = SystemHealthMonitoringGateway()
        ingest_result = gateway.ingest(raw_data)

        if raw_data == b"":
            return {}

        return ingest_result


def stream_system_health_telemetry(aggregated_health):
    if not isinstance(aggregated_health, dict):
        aggregated_health = {"run_id": str(aggregated_health)}
    run_id = aggregated_health.get("run_id")
    return {
        "streamed": True,
        "processed_run_id": run_id,
        "timestamp": time.time()
    }


def system_telemetry_streamer(payload=None, **kwargs):
    if isinstance(payload, dict):
        return stream_system_health_telemetry(payload)
    return SystemTelemetryStreamer()
