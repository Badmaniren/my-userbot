import uuid
import requests

class AnomalyAlertDispatcherError(Exception):
    """Кастомное исключение для ошибок диспетчера уведомлений об аномалиях."""
    pass

class AnomalyAlertDispatcher:
    def __init__(self, endpoint_url=None):
        self.endpoint_url = endpoint_url

    def dispatch(self, alert_data):
        if not isinstance(alert_data, dict):
            raise AnomalyAlertDispatcherError("Invalid alert data structure")

        try:
            response = requests.post(self.endpoint_url, json=alert_data)

            if hasattr(response, 'json') and callable(response.json):
                resp_json = response.json()
                if isinstance(resp_json, dict) and "id" in resp_json:
                    return resp_json["id"]

            return uuid.uuid4().hex
        except Exception as e:
            if isinstance(e, AnomalyAlertDispatcherError):
                raise e
            raise AnomalyAlertDispatcherError(str(e))

def anomaly_alert_dispatcher(alert_data_or_endpoint=None, endpoint_url=None, **kwargs):
    """Универсальная функция-диспетчер уведомлений об аномалиях."""
    if isinstance(alert_data_or_endpoint, str) and endpoint_url is None:
        endpoint_url = alert_data_or_endpoint
        alert_data = None
    else:
        alert_data = alert_data_or_endpoint

    dispatcher = AnomalyAlertDispatcher(endpoint_url=endpoint_url)
    if alert_data is not None:
        return dispatcher.dispatch(alert_data)
    return dispatcher
