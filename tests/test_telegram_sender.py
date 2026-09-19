import io
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import requests

from skills.telegram_sender import TelegramSender


class TestTelegramSender(unittest.TestCase):

    def _generate_random_string(self, length=None):
        if length is None:
            length = random.randint(10, 25)
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_token(self):
        bot_id = random.randint(100000000, 999999999)
        secret = self._generate_random_string(35)
        return f"{bot_id}:{secret}"

    def _generate_random_chat_id(self):
        if random.choice([True, False]):
            return str(random.randint(10000000, 999999999))
        return f"-100{random.randint(100000000, 999999999)}"

    def test_init_sets_randomized_attributes(self):
        token = self._generate_random_token()
        chat_id = self._generate_random_chat_id()
        timeout = random.randint(5, 60)

        sender = TelegramSender(bot_token=token, chat_id=chat_id, timeout=timeout)

        self.assertEqual(sender.bot_token, token)
        self.assertEqual(sender.chat_id, chat_id)
        self.assertEqual(sender.timeout, timeout)
        expected_url = f"https://api.telegram.org/bot{token}"
        self.assertTrue(sender.base_url.rstrip("/").startswith(expected_url))

    def test_init_raises_value_error_on_empty_token(self):
        invalid_token = random.choice(["", "   ", None])
        with self.assertRaises((ValueError, TypeError)):
            TelegramSender(bot_token=invalid_token)

    def test_send_message_success_with_default_chat_id(self):
        token = self._generate_random_token()
        default_chat_id = self._generate_random_chat_id()
        timeout = random.randint(10, 30)
        sender = TelegramSender(bot_token=token, chat_id=default_chat_id, timeout=timeout)

        msg_text = f"Random_Msg_{self._generate_random_string()}"
        message_id = random.randint(1000, 99999)
        fake_api_response = {
            "ok": True,
            "result": {
                "message_id": message_id,
                "text": msg_text,
                "chat": {"id": int(default_chat_id) if default_chat_id.lstrip('-').isdigit() else default_chat_id}
            }
        }

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = fake_api_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = sender.send_message(text=msg_text)

            expected_endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args

            self.assertEqual(called_args[0], expected_endpoint)
            self.assertEqual(called_kwargs.get("timeout"), timeout)

            json_payload = called_kwargs.get("json", {})
            self.assertEqual(str(json_payload.get("chat_id")), str(default_chat_id))
            self.assertEqual(json_payload.get("text"), msg_text)
            self.assertIn("parse_mode", json_payload)
            self.assertEqual(result, fake_api_response)

    def test_send_message_override_chat_id_and_parse_mode(self):
        token = self._generate_random_token()
        default_chat_id = self._generate_random_chat_id()
        override_chat_id = self._generate_random_chat_id()
        parse_mode = random.choice(["MarkdownV2", "Markdown", "HTML"])
        sender = TelegramSender(bot_token=token, chat_id=default_chat_id)

        msg_text = f"Payload_{self._generate_random_string(30)}"
        fake_response = {"ok": True, "result": {"message_id": random.randint(1, 100)}}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = fake_response
            mock_post.return_value = mock_resp

            result = sender.send_message(
                text=msg_text,
                chat_id=override_chat_id,
                parse_mode=parse_mode
            )

            mock_post.assert_called_once()
            json_payload = mock_post.call_args[1].get("json", {})
            self.assertEqual(str(json_payload.get("chat_id")), str(override_chat_id))
            self.assertNotEqual(str(json_payload.get("chat_id")), str(default_chat_id))
            self.assertEqual(json_payload.get("text"), msg_text)
            self.assertEqual(json_payload.get("parse_mode"), parse_mode)
            self.assertEqual(result, fake_response)

    def test_send_message_without_chat_id_raises_value_error(self):
        token = self._generate_random_token()
        sender = TelegramSender(bot_token=token, chat_id=None)
        msg_text = self._generate_random_string()

        with patch("requests.post") as mock_post:
            with self.assertRaises(ValueError):
                sender.send_message(text=msg_text, chat_id=None)
            mock_post.assert_not_called()

    def test_send_message_empty_text_raises_value_error(self):
        token = self._generate_random_token()
        chat_id = self._generate_random_chat_id()
        sender = TelegramSender(bot_token=token, chat_id=chat_id)

        empty_text = random.choice(["", "   ", None])
        with patch("requests.post") as mock_post:
            with self.assertRaises(ValueError):
                sender.send_message(text=empty_text)
            mock_post.assert_not_called()

    def test_send_alert_formats_and_dispatches_message(self):
        token = self._generate_random_token()
        chat_id = self._generate_random_chat_id()
        sender = TelegramSender(bot_token=token, chat_id=chat_id)

        alert_title = f"AlertTitle_{self._generate_random_string(8)}"
        alert_body = f"AlertDetails_{self._generate_random_string(40)}"
        alert_level = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        custom_chat_id = self._generate_random_chat_id()

        with patch.object(sender, "send_message") as mock_send_message:
            expected_return = {"ok": True, "result": {"message_id": random.randint(100, 500)}}
            mock_send_message.return_value = expected_return

            result = sender.send_alert(
                title=alert_title,
                message=alert_body,
                level=alert_level,
                chat_id=custom_chat_id
            )

            mock_send_message.assert_called_once()
            called_kwargs = mock_send_message.call_args[1]
            sent_text = called_kwargs.get("text", "")

            self.assertIn(alert_title, sent_text)
            self.assertIn(alert_body, sent_text)
            self.assertIn(alert_level, sent_text)
            self.assertEqual(called_kwargs.get("chat_id"), custom_chat_id)
            self.assertEqual(result, expected_return)

    def test_send_message_http_error_handling(self):
        token = self._generate_random_token()
        chat_id = self._generate_random_chat_id()
        sender = TelegramSender(bot_token=token, chat_id=chat_id)
        msg_text = self._generate_random_string()
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_desc = f"Error_{self._generate_random_string()}"

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = status_code
            mock_resp.json.return_value = {"ok": False, "error_code": status_code, "description": error_desc}
            http_error = requests.exceptions.HTTPError(response=mock_resp)
            mock_resp.raise_for_status.side_effect = http_error
            mock_post.return_value = mock_resp

            with self.assertRaises((requests.exceptions.HTTPError, RuntimeError, Exception)):
                sender.send_message(text=msg_text)

    def test_send_message_network_connection_timeout(self):
        token = self._generate_random_token()
        chat_id = self._generate_random_chat_id()
        sender = TelegramSender(bot_token=token, chat_id=chat_id)
        msg_text = self._generate_random_string()

        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout(f"Timeout_{self._generate_random_string()}")

            with self.assertRaises(requests.exceptions.RequestException):
                sender.send_message(text=msg_text)

    def test_send_document_stream_upload(self):
        token = self._generate_random_token()
        chat_id = self._generate_random_chat_id()
        sender = TelegramSender(bot_token=token, chat_id=chat_id)

        if hasattr(sender, "send_document"):
            random_bytes = self._generate_random_string(50).encode("utf-8")
            file_stream = io.BytesIO(random_bytes)
            file_name = f"doc_{self._generate_random_string(5)}.txt"
            caption = f"Caption_{self._generate_random_string()}"

            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"ok": True, "result": {"message_id": random.randint(100, 999)}}
                mock_post.return_value = mock_resp

                sender.send_document(
                    document=file_stream,
                    filename=file_name,
                    caption=caption
                )

                mock_post.assert_called_once()
                called_url = mock_post.call_args[0][0]
                self.assertIn("sendDocument", called_url)
                files_payload = mock_post.call_args[1].get("files", {})
                self.assertIn("document", files_payload)


if __name__ == "__main__":
    unittest.main()