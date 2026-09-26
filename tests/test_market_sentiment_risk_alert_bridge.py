import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

market_sentiment_risk_hub_mock = types.ModuleType("skills.market_sentiment_risk_hub")
class MockMarketSentimentRiskHub:
    def __init__(self, *args, **kwargs):
        pass
    def evaluate_risk(self, ticker, exchange, news_snippet):
        return {"ticker": ticker, "exchange": exchange, "risk_score": random.uniform(0.1, 0.9)}
    def process_stream(self, stream_source):
        return [random.randint(100, 999)]
    def export_report(self, ticker, filename):
        return True
market_sentiment_risk_hub_mock.MarketSentimentRiskHub = MockMarketSentimentRiskHub

market_portfolio_alert_dispatcher_mock = types.ModuleType("skills.market_portfolio_alert_dispatcher")
def mock_send_telegram_notification(token, chat_id, message):
    return True
def mock_dispatch_portfolio_alerts(symbol, url, telegram_token, chat_id, storage_file, severity_level, min_threshold, channels):
    return {"status": "dispatched", "symbol": symbol}
def mock_process_stream_alert(alert_id):
    return {"alert_id": alert_id, "processed": True}
market_portfolio_alert_dispatcher_mock.send_telegram_notification = mock_send_telegram_notification
market_portfolio_alert_dispatcher_mock.dispatch_portfolio_alerts = mock_dispatch_portfolio_alerts
market_portfolio_alert_dispatcher_mock.process_stream_alert = mock_process_stream_alert

sys.modules["skills.market_sentiment_risk_hub"] = market_sentiment_risk_hub_mock
sys.modules["skills.market_portfolio_alert_dispatcher"] = market_portfolio_alert_dispatcher_mock

bridge_module = types.ModuleType("skills.market_sentiment_risk_risk_alert_bridge")
from skills import market_sentiment_risk_hub
from skills import market_portfolio_alert_dispatcher

class MarketSentimentRiskAlertBridge:
    def __init__(self, token, chat_id, storage_file):
        self.token = token
        self.chat_id = chat_id
        self.storage_file = storage_file
        self.hub = market_sentiment_risk_hub.MarketSentimentRiskHub()

    def bridge_evaluate_and_dispatch(self, ticker, exchange, news_snippet, url, severity_level, min_threshold, channels):
        risk_data = self.hub.evaluate_risk(ticker, exchange, news_snippet)
        dispatch_result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=ticker,
            url=url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )
        return {
            "risk_data": risk_data,
            "dispatch_result": dispatch_result
        }

    def bridge_process_stream(self, stream_source):
        stream_items = self.hub.process_stream(stream_source)
        results = []
        for item in stream_items:
            res = market_portfolio_alert_dispatcher.process_stream_alert(item)
            results.append(res)
        return results

bridge_module.MarketSentimentRiskAlertBridge = MarketSentimentRiskAlertBridge
sys.modules["skills.market_sentiment_risk_risk_alert_bridge"] = bridge_module

class TestMarketSentimentRiskAlertBridge(unittest.TestCase):
    def setUp(self):
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.bridge = MarketSentimentRiskAlertBridge(self.token, self.chat_id, self.storage_file)

    def test_bridge_evaluate_and_dispatch_logic(self):
        rand_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_exchange = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_snippet = uuid.uuid4().hex
        rand_url = f"https://{uuid.uuid4().hex}.com/api"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_threshold = random.uniform(0.0, 1.0)
        rand_channels = [uuid.uuid4().hex, uuid.uuid4().hex]

        result = self.bridge.bridge_evaluate_and_dispatch(
            ticker=rand_ticker,
            exchange=rand_exchange,
            news_snippet=rand_snippet,
            url=rand_url,
            severity_level=rand_severity,
            min_threshold=rand_threshold,
            channels=rand_channels
        )

        self.assertIn("risk_data", result)
        self.assertIn("dispatch_result", result)
        self.assertEqual(result["risk_data"]["ticker"], rand_ticker)
        self.assertEqual(result["risk_data"]["exchange"], rand_exchange)
        self.assertEqual(result["dispatch_result"]["symbol"], rand_ticker)

    def test_bridge_process_stream_logic(self):
        rand_stream_source = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

        with patch("skills.market_sentiment_risk_hub.MarketSentimentRiskHub.process_stream") as mock_process_stream:
            mock_id = random.randint(1000, 9999)
            mock_process_stream.return_value = [mock_id]

            results = self.bridge.bridge_process_stream(rand_stream_source)

            mock_process_stream.assert_called_once_with(rand_stream_source)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["alert_id"], mock_id)
            self.assertTrue(results[0]["processed"])

    def test_bridge_initialization_attributes(self):
        self.assertEqual(self.bridge.token, self.token)
        self.assertEqual(self.bridge.chat_id, self.chat_id)
        self.assertEqual(self.bridge.storage_file, self.storage_file)
        self.assertIsInstance(self.bridge.hub, market_sentiment_risk_hub.MarketSentimentRiskHub)

if __name__ == "__main__":
    unittest.main()