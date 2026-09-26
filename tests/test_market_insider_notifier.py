import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_insider_notifier import MarketInsiderNotifier, notify_market_insider

class TestMarketInsiderNotifier(unittest.TestCase):

    def setUp(self):
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.min_severity = random.choice(self.severity_levels)

    def test_composition_imports_and_pipeline_execution(self):
        raw_stream_data = {
            "event_id": uuid.uuid4().hex,
            "volume": random.randint(1000, 100000),
            "severity": random.choice(self.severity_levels)
        }
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process_alert_stream.return_value = raw_stream_data

        with patch("skills.market_insider_notifier.MarketInsiderAlertPipeline", return_value=mock_pipeline_instance) as MockPipeline:
            notifier = MarketInsiderNotifier(
                token=self.token,
                chat_id=self.chat_id,
                min_severity=self.min_severity
            )
            
            MockPipeline.assert_called_once()
            
            result = notifier.handle_stream_event(self.ticker, raw_stream_data)
            mock_pipeline_instance.process_alert_stream.assert_called_once_with(self.ticker, raw_stream_data)
            self.assertIsNotNone(result)

    def test_telegram_notifier_integration(self):
        message_body = f"ANOMALY DETECTED: {uuid.uuid4().hex}"
        
        with patch("skills.market_insider_notifier.start_new", return_value=True) as mock_start_new:
            notifier = MarketInsiderNotifier(
                token=self.token,
                chat_id=self.chat_id,
                min_severity="LOW"
            )
            
            success = notifier.dispatch_notification(message_body)
            
            mock_start_new.assert_called_once_with(self.token, self.chat_id, message_body)
            self.assertTrue(success)

    def test_severity_filtering_logic(self):
        high_severity_data = {
            "event_id": uuid.uuid4().hex,
            "severity": "CRITICAL"
        }
        low_severity_data = {
            "event_id": uuid.uuid4().hex,
            "severity": "LOW"
        }

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process_alert_stream.side_effect = [high_severity_data, low_severity_data]

        with patch("skills.market_insider_notifier.MarketInsiderAlertPipeline", return_value=mock_pipeline_instance), \
             patch("skills.market_insider_notifier.start_new", return_value=True) as mock_telegram:
            
            notifier = MarketInsiderNotifier(
                token=self.token,
                chat_id=self.chat_id,
                min_severity="HIGH"
            )
            
            # Should trigger notification
            res1 = notifier.process_and_notify(self.ticker, high_severity_data)
            self.assertTrue(res1)
            mock_telegram.assert_called_once()
            
            mock_telegram.reset_mock()
            
            # Should skip notification due to low severity
            res2 = notifier.process_and_notify(self.ticker, low_severity_data)
            self.assertFalse(res2)
            mock_telegram.assert_not_called()

    def test_stream_evaluation_wrapper(self):
        exchange_name = f"EXCHANGE_{uuid.uuid4().hex[:6]}"
        evaluation_result = {
            "status": "ANOMALY_FOUND",
            "score": random.uniform(1.0, 10.0)
        }

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.evaluate_market_stream.return_value = evaluation_result

        with patch("skills.market_insider_notifier.MarketInsiderAlertPipeline", return_value=mock_pipeline_instance):
            notifier = MarketInsiderNotifier(
                token=self.token,
                chat_id=self.chat_id,
                min_severity="MEDIUM"
            )
            
            res = notifier.evaluate_exchange(exchange_name)
            mock_pipeline_instance.evaluate_market_stream.assert_called_once_with(exchange_name)
            self.assertEqual(res, evaluation_result)

    def test_module_level_function_wrapper(self):
        random_message = uuid.uuid4().hex
        
        with patch("skills.market_insider_notifier.send_telegram_notification", return_value=True) as mock_send:
            outcome = notify_market_insider(self.token, self.chat_id, random_message)
            mock_send.assert_called_once_with(self.token, self.chat_id, random_message)
            self.assertTrue(outcome)

    def test_io_byte_stream_handling(self):
        random_bytes = uuid.uuid4().bytes + b''.join(random.choices(string.ascii_letters.encode(), k=32))
        byte_stream = io.BytesIO(random_bytes)
        
        mock_pipeline_instance = MagicMock()
        
        with patch("skills.market_insider_notifier.MarketInsiderAlertPipeline", return_value=mock_pipeline_instance):
            notifier = MarketInsiderNotifier(
                token=self.token,
                chat_id=self.chat_id,
                min_severity="LOW"
            )
            
            consumed_data = notifier.consume_stream_bytes(byte_stream)
            self.assertEqual(consumed_data, random_bytes)

if __name__ == "__main__":
    unittest.main()