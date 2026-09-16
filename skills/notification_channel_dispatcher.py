import json
import requests


class NotificationChannelDispatcher:
    """Модуль для диспетчеризации уведомлений о критических сбоях

    и статусах самовосстановления системы в различные внешние каналы.
    """

    def __init__(self):
        self.channels = {}

    def register_channel(self, channel_name: str, config: dict):
        """Регистрирует новый канал уведомлений."""
        self.channels[channel_name] = config

    def dispatch(self, channel_name: str, payload: dict) -> bool:
        """Отправляет полезную нагрузку в указанный канал."""
        if channel_name not in self.channels:
            return False

        channel_config = self.channels[channel_name]
        url = channel_config.get("url")
        if not url:
            return False

        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception:
            return False

    def broadcast(self, payload: dict) -> dict:
        """Рассылает уведомление по всем зарегистрированным каналам."""
        results = {}
        for channel_name in self.channels:
            results[channel_name] = self.dispatch(channel_name, payload)
        return results

    def parse_stream_data(self, stream) -> dict:
        """Парсит данные потока в формате JSON."""
        try:
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            data = json.loads(content)
            if not isinstance(data, dict):
                return None
            return data
        except Exception:
            return None

    def format_payload(
        self, level: str, incident_id: str, message: str
    ) -> dict:
        """Форматирует полезную нагрузку для уведомления."""
        return {
            "level": level,
            "incident_id": incident_id,
            "message": message,
        }


notification_channel_dispatcher = NotificationChannelDispatcher