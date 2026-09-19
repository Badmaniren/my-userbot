import requests


class TelegramSender:
    def __init__(self, bot_token=None, chat_id=None, timeout=30, base_url="https://api.telegram.org"):
        if not bot_token or not str(bot_token).strip():
            raise ValueError("Bot token is required and cannot be empty.")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

        base = base_url.rstrip("/")
        if f"/bot{bot_token}" in base:
            self.base_url = base
        else:
            self.base_url = f"{base}/bot{bot_token}"

    def send_message(self, text, chat_id=None, parse_mode=None):
        if not text or not str(text).strip():
            raise ValueError("Message text cannot be empty.")

        target_chat_id = chat_id if chat_id is not None else self.chat_id
        if target_chat_id is None:
            raise ValueError("Chat ID is required.")

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        else:
            payload["parse_mode"] = "HTML"

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def send_alert(self, title, message, level="INFO", chat_id=None):
        formatted_text = f"<b>[{level}] {title}</b>\n\n{message}"
        return self.send_message(text=formatted_text, chat_id=chat_id, parse_mode="HTML")

    def send_document(self, document, filename=None, caption=None, chat_id=None):
        target_chat_id = chat_id if chat_id is not None else self.chat_id
        if target_chat_id is None:
            raise ValueError("Chat ID is required.")

        url = f"{self.base_url}/sendDocument"
        data = {"chat_id": target_chat_id}
        if caption:
            data["caption"] = caption

        files = {"document": (filename or "document", document)}

        response = requests.post(url, data=data, files=files, timeout=self.timeout)
        response.raise_for_status()
        return response.json()