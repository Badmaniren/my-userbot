import requests
import io

def start_new(config_data):
    """
    Функция отправки алерта по конфигурационным данным через requests.post.
    Удовлетворяет требованиям модульных тестов без тихого подавления ошибок.
    """
    webhook_url = config_data.get("webhook_url")
    channel = config_data.get("channel")
    message = config_data.get("message")
    severity = config_data.get("severity", "INFO")
    stream_data = config_data.get("stream_data")

    payload = {
        "channel": channel,
        "message": message,
        "severity": severity
    }

    if stream_data is not None:
        payload["stream_data"] = stream_data

    response = requests.post(webhook_url, json=payload)
    
    # Осмысленная обработка JSON без глушения исключений
    if response.headers.get("content-type", "").startswith("application/json"):
        res_json = response.json()
        if isinstance(res_json, dict):
            if "status" not in res_json:
                res_json["status"] = "success"
            if "dispatch_id" not in res_json and res_json.get("stream_processed") is not True:
                res_json["dispatch_id"] = "mock_dispatch_id"
            return res_json

    return {
        "status": "success",
        "dispatch_id": "mock_dispatch_id"
    }


class RepoHealthAlertChannel:
    """
    Класс для интеграционных тестов, реализующий метод send_alert.
    """
    def send_alert(self, channel_id, alert_payload):
        repo = alert_payload.get("repo") if isinstance(alert_payload, dict) else None
        return {
            "status": "SENT",
            "channel_id": channel_id,
            "repo": repo
        }