import requests
import io

class RepoHealthAlertChannel:
    def __init__(self, dispatcher=None):
        self.dispatcher = dispatcher

    def send_telegram(self, token: str, chat_id: str, text: str) -> bool:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("ok", False)
            return False
        except Exception as e:
            if self.dispatcher and hasattr(self.dispatcher, 'log_error'):
                self.dispatcher.log_error(str(e))
            return False

    def send_webhook(self, url: str, payload: dict) -> bool:
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            if self.dispatcher and hasattr(self.dispatcher, 'log_error'):
                self.dispatcher.log_error(str(e))
            return False

    def dispatch_alert(self, alert_id: str, data: dict):
        if self.dispatcher and hasattr(self.dispatcher, 'process_alert'):
            self.dispatcher.process_alert(alert_id, data)

    def _prepare_payload(self, data: dict) -> dict:
        return dict(data)

    def process_stream_alert(self, stream: io.BytesIO) -> str:
        content = stream.read()
        return content.decode('utf-8')