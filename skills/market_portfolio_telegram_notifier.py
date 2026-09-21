import requests


def start_new(token: str, chat_id: str, message: str) -> bool:
    """
    Отправляет уведомление в Telegram.
    При невалидных аргументах, ошибках API или сетевых сбоях возвращает False.
    """
    if not isinstance(token, str) or not token.strip():
        return False
    if not isinstance(chat_id, str) or not chat_id.strip():
        return False
    if not isinstance(message, str) or not message.strip():
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            return False
        data = response.json()
        return bool(data.get("ok"))
    except (requests.exceptions.RequestException, ValueError):
        return False


def send_telegram_notification(token: str, chat_id: str, message: str) -> bool:
    """Алиас для отправки уведомлений."""
    return start_new(token, chat_id, message)
