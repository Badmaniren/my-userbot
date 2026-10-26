import io
import os
import json
from skills.anomaly_filter import start_new as filter_start_new


class AnomalyTelemetryHubError(Exception):
    """Исключение для ошибок модуля anomaly_telemetry_hub."""
    pass


class AnomalyTelemetryHub:
    """
    Модуль сбора, агрегации и предварительной фильтрации телеметрии системы
    для комплексного анализа аномалий.
    """
    def __init__(self, repo_path: str = None, log_path: str = None, threshold: float = 0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

    def process_telemetry(self, payload):
        return start_new(payload)

    def filter_telemetry(self, payload):
        return start_new(payload)

    def collect(self, payload):
        return start_new(payload)


def start_new(payload):
    """
    Модуль сбора, агрегации и предварительной фильтрации телеметрии системы
    для комплексного анализа аномалий.
    """
    if payload is None:
        return {}

    if isinstance(payload, (int, float)):
        return {"value": payload}

    if isinstance(payload, str):
        if not payload:
            return {}
        return {"data": payload}

    if isinstance(payload, io.IOBase):
        content = payload.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        return {"stream_content": content}

    if isinstance(payload, list):
        filtered_list = []
        for item in payload:
            if isinstance(item, dict):
                if any(str(k).startswith("noise_") for k in item.keys()):
                    continue
                try:
                    res = filter_start_new(item)
                    if res:
                        filtered_list.append(res)
                    else:
                        filtered_list.append(item)
                except Exception:
                    filtered_list.append(item)
            else:
                try:
                    res = filter_start_new(item)
                    if res:
                        filtered_list.append(res)
                    else:
                        filtered_list.append(item)
                except Exception:
                    filtered_list.append(item)
        return filtered_list

    if isinstance(payload, dict):
        if any(str(k).startswith("noise_") for k in payload.keys()):
            return {}
        try:
            res = filter_start_new(payload)
            if res is not None:
                return res
        except Exception:
            return payload
        return payload

    return {}
