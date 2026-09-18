import json
import io
import os
import requests

class ForensicCollector:
    def start_new(self, incident_id, source_url, save_path=None, data=None):
        try:
            if data is not None:
                payload = dict(data)
                payload["incident_id"] = incident_id
            else:
                response = requests.get(source_url, timeout=10)
                if hasattr(response, 'raw') and response.raw and not response.content:
                    # Stream processing case
                    stream_content = response.raw.read()
                    payload = {
                        "incident_id": incident_id,
                        "telemetry_source": source_url,
                        "metadata": stream_content.decode('utf-8', errors='ignore'),
                        "stream_processed": True
                    }
                else:
                    try:
                        payload = json.loads(response.content.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        raise ValueError("Malformed telemetry data")
                    
                    if "incident_id" not in payload:
                        payload["incident_id"] = incident_id
                    if "telemetry_source" not in payload:
                        payload["telemetry_source"] = source_url

            if save_path:
                with open(save_path, 'w') as f:
                    json.dump(payload, f)

            return payload
        except requests.RequestException as e:
            raise ConnectionError(f"Network failure: {e}")
        except ValueError:
            raise
        except Exception as e:
            if isinstance(e, (ConnectionError, ValueError)):
                raise
            raise ConnectionError(str(e))


def incident_forensic_collector(incident_data, storage_path):
    from skills.incident_aggregator import incident_aggregator
    from skills.system_health_telemetry_collector import system_health_telemetry_collector

    incident_id = incident_data.get("incident_id", "unknown-inc")
    forensic_id = f"forensic-{incident_id}"
    
    result = {
        "forensic_id": forensic_id,
        "incident_id": incident_id,
        "data": incident_data
    }

    file_name = f"{incident_id}_forensic.log"
    os.makedirs(storage_path, exist_ok=True)
    file_path = os.path.join(storage_path, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(result))

    return result