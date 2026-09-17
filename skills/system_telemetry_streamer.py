import time
from skills.system_health_telemetry_collector import system_health_telemetry_collector

class SystemTelemetryStreamer:
    def __init__(self, interval: float = 1.0):
        self.interval = interval

    def stream(self):
        while True:
            data = system_health_telemetry_collector.collect()
            yield data
            time.sleep(self.interval)

def system_telemetry_streamer(session_id: str = None, stream_mode: str = "realtime", **kwargs):
    collector_data = system_health_telemetry_collector(session_id=session_id, stream_mode=stream_mode, **kwargs)
    if isinstance(collector_data, dict):
        result = dict(collector_data)
    else:
        result = {}

    result["status"] = result.get("status", "nominal")
    result["session_id"] = session_id
    result["streaming_active"] = True
    return result