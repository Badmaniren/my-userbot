import json
import time

class IncidentAggregator:
    """
    Handles registration of anomalies detected during telemetry processing.
    """
    def register_incident(self, incident_data):
        """
        Placeholder for incident registration logic.
        In production, this would send data to a monitoring service or database.
        """
        pass

# Instance available for patching in unit tests
incident_aggregator = IncidentAggregator()

class TelemetryProcessor:
    """
    Processor for raw telemetry data packets ensuring schema consistency.
    Used primarily for system-level metrics.
    """
    def process_packet(self, raw_packet):
        """
        Normalizes a single packet. Returns None if mandatory fields are missing
        or if data types are incompatible.
        """
        mandatory_fields = ["packet_id", "metric_name", "data_value", "timestamp"]
        if not all(field in raw_packet for field in mandatory_fields):
            return None
        
        try:
            return {
                "id": str(raw_packet["packet_id"]),
                "metric": str(raw_packet["metric_name"]),
                "value": float(raw_packet["data_value"]),
                "timestamp": int(raw_packet["timestamp"]),
                "processed_at": time.time()
            }
        except (ValueError, TypeError):
            return None

    def ingest_from_file(self, file_path):
        """
        Reads raw JSON telemetry from a file and processes it.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return self.process_packet(data)

    def process_and_dispatch(self, raw_packet):
        """
        Processes a packet and dispatches it to the incident aggregator if 
        values exceed the anomaly threshold (> 1000.0).
        """
        processed = self.process_packet(raw_packet)
        if processed:
            # Threshold for anomaly detection as defined in requirements
            if processed["value"] > 1000.0:
                incident_aggregator.register_incident(processed)
        return processed

    def process_batch(self, packets):
        """
        Processes a list of packets, filtering out those that do not match the schema.
        """
        results = []
        for packet in packets:
            processed = self.process_packet(packet)
            if processed:
                results.append(processed)
        return results

def process_telemetry_packet(raw_packet):
    """
    Standalone function for processing hardware-level telemetry.
    Used in the integration pipeline.
    """
    # Integration schema requires sensor_id, raw_value, and unix_timestamp
    required = ["sensor_id", "raw_value", "unix_timestamp"]
    if not all(k in raw_packet for k in required):
        return None
    
    try:
        processed = {
            "device_uuid": str(raw_packet["sensor_id"]),
            # Schema requires rounding to 2 decimal places
            "metric_value": round(float(raw_packet["raw_value"]), 2),
            "normalized_timestamp": int(raw_packet["unix_timestamp"])
        }
        
        # Preserve session metadata for the streaming pipeline
        metadata = raw_packet.get("metadata")
        if isinstance(metadata, dict) and "session" in metadata:
            processed["origin_session"] = metadata["session"]
            
        return processed
    except (ValueError, TypeError):
        return None


def telemetry_processor(payload=None, **kwargs):
    res = dict(payload) if isinstance(payload, dict) else {}
    res.update(kwargs)
    return res


def process(data=None, **kwargs):
    return telemetry_processor(data, **kwargs)