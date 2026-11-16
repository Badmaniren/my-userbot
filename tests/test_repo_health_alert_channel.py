import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json
from skills.repo_health_alert_channel import RepoHealthAlertChannel

class TestRepoHealthAlertChannel(unittest.TestCase):

    def setUp(self):
        self.dispatcher = MagicMock()
        self.channel = RepoHealthAlertChannel(dispatcher=self.dispatcher)

    def test_send_telegram_alert_success(self):
        random_token = uuid.uuid4().hex
        random_chat_id = str(random.randint(100000, 999999))
        random_msg = ''.join(random.choices(string.ascii_letters, k=20))
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"ok": True}
            
            result = self.channel.send_telegram(random_token, random_chat_id, random_msg)
            
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(random_token, args[0])
            self.assertEqual(kwargs['json']['chat_id'], random_chat_id)
            self.assertEqual(kwargs['json']['text'], random_msg)

    def test_send_webhook_failure_handling(self):
        random_url = f"https://{uuid.uuid4().hex}.com/hook"
        random_payload = {"event": uuid.uuid4().hex, "severity": random.choice(["high", "low"])}
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection Timeout")
            
            # Проверяем, что метод не падает, а возвращает False при ошибке
            result = self.channel.send_webhook(random_url, random_payload)
            
            self.assertFalse(result)
            self.dispatcher.log_error.assert_called()

    def test_dispatch_integration(self):
        random_alert_id = uuid.uuid4().hex
        random_data = {"metric": random.random(), "status": "critical"}
        
        # Проверяем, что канал корректно взаимодействует с диспетчером
        self.channel.dispatch_alert(random_alert_id, random_data)
        
        self.dispatcher.process_alert.assert_called_once_with(random_alert_id, random_data)

    def test_payload_sanitization(self):
        random_key = uuid.uuid4().hex
        random_val = ''.join(random.choices(string.printable, k=15))
        input_data = {random_key: random_val}
        
        # Проверяем, что данные проходят через систему без искажений
        processed = self.channel._prepare_payload(input_data)
        
        self.assertEqual(processed[random_key], random_val)
        self.assertIsInstance(processed, dict)

    def test_stream_processing_simulation(self):
        random_content = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_content)
        
        # Проверяем обработку потоковых данных (например, логов)
        result = self.channel.process_stream_alert(mock_stream)
        
        self.assertEqual(result, random_content.decode('utf-8'))

    def test_retry_logic_on_server_error(self):
        random_url = f"https://{uuid.uuid4().hex}.io"
        
        with patch('requests.post') as mock_post:
            # Имитируем 500 ошибку
            mock_post.return_value.status_code = 500
            
            result = self.channel.send_webhook(random_url, {"test": "data"})
            
            self.assertFalse(result)
            self.assertEqual(mock_post.call_count, 1)

if __name__ == '__main__':
    unittest.main()