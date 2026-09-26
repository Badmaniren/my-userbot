import unittest
import uuid
import random
from skills.market_insider_notifier import MarketInsiderNotifier
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline


class TestMarketInsiderNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.token = f"test_token_{uuid.uuid4()}"
        self.chat_id = f"test_chat_{random.randint(10000, 99999)}"
        self.pipeline = MarketInsiderAlertPipeline()
        self.notifier = MarketInsiderNotifier(
            token=self.token,
            chat_id=self.chat_id,
            min_severity="LOW",
            pipeline=self.pipeline
        )

    def test_integration_pipeline_and_notifier(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        event_id = str(uuid.uuid4())
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        selected_severity = random.choice(severities)

        raw_data = {
            "id": event_id,
            "severity": selected_severity,
            "description": f"Integration test anomaly {uuid.uuid4()}"
        }

        # Mocking or replacing the telegram sender to avoid real network calls while keeping actual internal execution flow
        notifications_sent = []

        def mock_telegram_sender(token, chat_id, message):
            notifications_sent.append({
                "token": token,
                "chat_id": chat_id,
                "message": message
            })
            return True

        self.notifier.telegram_sender = mock_telegram_sender

        result = self.notifier.process_and_notify(
            ticker=ticker,
            raw_stream_data=raw_data,
            min_criticality="LOW"
        )

        self.assertTrue(result)
        self.assertEqual(len(notifications_sent), 1)
        self.assertIn(ticker, notifications_sent[0]["message"])
        self.assertIn(event_id, notifications_sent[0]["message"])
        self.assertEqual(notifications_sent[0]["token"], self.token)
        self.assertEqual(notifications_sent[0]["chat_id"], self.chat_id)

    def test_integration_filtering_severity(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        event_id = str(uuid.uuid4())

        raw_data = {
            "id": event_id,
            "severity": "LOW",
            "description": "Low severity event"
        }

        notifications_sent = []
        self.notifier.telegram_sender = lambda t, c, m: notifications_sent.append(m) or True

        # Устанавливаем минимальный порог HIGH, при этом событие имеет LOW -> уведомление не должно уйти
        result = self.notifier.process_and_notify(
            ticker=ticker,
            raw_stream_data=raw_data,
            min_criticality="HIGH"
        )

        self.assertFalse(result)
        self.assertEqual(len(notifications_sent), 0)


if __name__ == "__main__":
    unittest.main()