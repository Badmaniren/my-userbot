import requests


def start_new(token: str, chat_id: str, message: str) -> bool:
    """Отправляет уведомление в Telegram (функция для юнит-тестов)."""
    if not isinstance(token, str) or not token.strip():
        return False
    if not isinstance(chat_id, (str, int)) or not str(chat_id).strip():
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
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            return True
        return False
    except (requests.exceptions.RequestException, ValueError, TypeError, KeyError):
        return False


def send_telegram_notification(token: str, chat_id: str, message: str) -> bool:
    """Алиас для отправки уведомлений, используемый в интеграционных тестах."""
    return start_new(token, chat_id, message)


send_telegram_notifier = send_telegram_notification