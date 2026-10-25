import requests

class AnomalyAlertDispatcherError(Exception):
    """Исключение, возникающее при ошибках диспетчеризации аномалий."""
    pass

class AnomalyAlertDispatcher:
    def __init__(self, endpoint, api_token=None, timeout=5):
        self.endpoint = endpoint
        self.api_token = api_token
        self.timeout = timeout

    def dispatch_alert(self, severity, message, telemetry=None):
        if not self.endpoint:
            raise AnomalyAlertDispatcherError("Invalid endpoint")
        
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        payload = {
            "severity": severity,
            "message": message,
            "telemetry": telemetry or {}
        }

        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=self.timeout)
            return True
        except Exception as e:
            raise AnomalyAlertDispatcherError(f"Failed to dispatch alert: {e}")


def dispatch_alert(audit_hub, target_service, dispatch_id):
    """Интеграционная функция для отправки отчета на основе аудита."""
    anomalies = []
    if hasattr(audit_hub, 'logger') and audit_hub.logger and hasattr(audit_hub.logger, 'get_anomalies'):
        anomalies = audit_hub.logger.get_anomalies()
    elif hasattr(audit_hub, 'get_anomalies'):
        anomalies = audit_hub.get_anomalies()

    payload = {
        "dispatch_id": dispatch_id,
        "target_service": target_service,
        "status": "dispatched",
        "anomalies": anomalies
    }
    return payload