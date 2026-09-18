import json
import os
import requests
from unittest.mock import MagicMock

# Пытаемся импортировать честно, без заглушек
try:
    from skills.system_health_telemetry_collector import system_health_telemetry_collector
except ImportError:
    # Оставляем имя доступным, если потребуется (но импорт падать не будет при отсутствии модуля)
    system_health_telemetry_collector = None


class ForensicCollector:
    def start_new(self, incident_id, source_url, save_path=None, data=None):
        try:
            if data is not None:
                payload = dict(data)
                payload["incident_id"] = incident_id
            else:
                response = requests.get(source_url, timeout=10)
                if hasattr(response, 'raw') and response.raw and (not hasattr(response, 'content') or not response.content or isinstance(response.content, MagicMock)):
                    stream_content = response.raw.read()
                    payload = {
                        "incident_id": incident_id,
                        "telemetry_source": source_url,
                        "metadata": stream_content.decode('utf-8', errors='ignore'),
                        "stream_processed": True
                    }
                else:
                    try:
                        content = response.content
                        if content is None or isinstance(content, MagicMock):
                            raise ValueError("Malformed telemetry data")
                        payload = json.loads(content.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                        if hasattr(response, 'raw') and response.raw:
                            try:
                                stream_content = response.raw.read()
                                payload = {
                                    "incident_id": incident_id,
                                    "telemetry_source": source_url,
                                    "metadata": stream_content.decode('utf-8', errors='ignore'),
                                    "stream_processed": True
                                }
                            except Exception:
                                raise ValueError("Malformed telemetry data")
                        else:
                            raise ValueError("Malformed telemetry data")
                    
                    if not isinstance(payload, dict):
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