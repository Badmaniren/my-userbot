import json
import os
import random
import tempfile
import threading
import unittest
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

from skills.market_parser import MarketParser
from skills.telegram_sender import TelegramSender


class TelegramMockHandler(BaseHTTPRequestHandler):
    requests_log = []
    response_override = None

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(post_body)
        except Exception:
            payload = post_body

        self.__class__.requests_log.append({
            "path": self.path,
            "headers": dict(self.headers),
            "payload": payload
        })

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if self.__class__.response_override:
            resp_body = self.__class__.response_override
        else:
            resp_body = {
                "ok": True,
                "result": {
                    "message_id": random.randint(10000, 99999),
                    "text": payload.get("text") if isinstance(payload, dict) else ""
                }
            }
        self.wfile.write(json.dumps(resp_body).encode("utf-8"))

    def log_message(self, format, *args):
        pass


class TestTelegramSenderIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TelegramMockHandler.requests_log = []
        TelegramMockHandler.response_override = None
        cls.server = HTTPServer(("127.0.0.1", 0), TelegramMockHandler)
        cls.server_port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.server_port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2.0)

    def setUp(self):
        TelegramMockHandler.requests_log.clear()
        TelegramMockHandler.response_override = None
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_send_message_transmits_exact_random_payload(self):
        token = f"tok_{uuid.uuid4().hex[:12]}"
        chat_id = random.randint(1000000, 9999999)
        random_text = f"Notification-{uuid.uuid4()}"
        expected_msg_id = random.randint(100000, 999999)

        TelegramMockHandler.response_override = {
            "ok": True,
            "result": {
                "message_id": expected_msg_id,
                "chat": {"id": chat_id},
                "text": random_text
            }
        }

        sender = TelegramSender(bot_token=token, chat_id=chat_id, base_url=self.base_url)
        response = sender.send_message(random_text)

        self.assertIsInstance(response, dict)
        self.assertTrue(response.get("ok"))
        self.assertEqual(response.get("result", {}).get("message_id"), expected_msg_id)

        self.assertEqual(len(TelegramMockHandler.requests_log), 1)
        last_req = TelegramMockHandler.requests_log[0]
        self.assertIn(f"/bot{token}/sendMessage", last_req["path"])
        self.assertEqual(last_req["payload"].get("chat_id"), chat_id)
        self.assertEqual(last_req["payload"].get("text"), random_text)

    def test_send_alert_formats_and_dispatches_content(self):
        token = f"tok_{uuid.uuid4().hex[:12]}"
        chat_id = random.randint(1000000, 9999999)
        alert_title = f"CRITICAL_ALERT_{uuid.uuid4().hex[:6]}"
        alert_body = f"Resource exceeded: {uuid.uuid4()}"
        level = "CRITICAL"

        sender = TelegramSender(bot_token=token, chat_id=chat_id, base_url=self.base_url)
        response = sender.send_alert(title=alert_title, message=alert_body, level=level)

        self.assertIsInstance(response, dict)
        self.assertTrue(response.get("ok"))

        self.assertEqual(len(TelegramMockHandler.requests_log), 1)
        req_payload = TelegramMockHandler.requests_log[0]["payload"]
        delivered_text = req_payload.get("text", "")
        self.assertIn(alert_title, delivered_text)
        self.assertIn(alert_body, delivered_text)
        self.assertIn(level, delivered_text)

    def test_integration_with_market_parser_storage_and_sender(self):
        storage_file = os.path.join(self.temp_dir.name, f"market_{uuid.uuid4().hex}.json")
        parser = MarketParser(storage_file=storage_file)

        symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        price = round(random.uniform(50.0, 5000.0), 2)
        parser.fetch_and_store(symbol, price)

        self.assertTrue(os.path.exists(storage_file))
        loaded_data = parser.load_data(storage_file)
        self.assertIn(symbol, loaded_data)
        if isinstance(loaded_data[symbol], dict):
            self.assertEqual(loaded_data[symbol].get("price"), price)
        else:
            self.assertEqual(loaded_data[symbol], price)

        token = f"tok_{uuid.uuid4().hex[:10]}"
        chat_id = random.randint(100000, 999999)
        sender = TelegramSender(bot_token=token, chat_id=chat_id, base_url=self.base_url)

        alert_msg = f"Price update: {symbol} is {price}"
        response = sender.send_message(alert_msg)

        self.assertTrue(response.get("ok"))
        self.assertEqual(len(TelegramMockHandler.requests_log), 1)
        sent_payload = TelegramMockHandler.requests_log[0]["payload"]
        self.assertEqual(sent_payload.get("text"), alert_msg)
        self.assertEqual(sent_payload.get("chat_id"), chat_id)


if __name__ == "__main__":
    unittest.main()