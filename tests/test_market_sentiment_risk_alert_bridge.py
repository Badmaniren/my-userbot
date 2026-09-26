import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.market_sentiment_risk_alert_bridge import (
    MarketSentimentRiskAlertBridge,
    process_sentiment_risk_and_dispatch_alert
)

class TestMarketSentimentRiskAlertBridge(unittest.TestCase):
    def test_bridge_evaluate_and_dispatch(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_exchange = random.choice(["NASDAQ", "NYSE", "MOEX", "LSE"])
        rand_snippet = f"Market crash risk due to {uuid.uuid4().hex}"
        rand_url = f"https://example.com/news/{uuid.uuid4().hex}"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_threshold = round(random.uniform(0.1, 0.9), 2)
        rand_channels = [random.choice(["telegram", "webhook", "email"])]

        mock_risk_return = {
            "ticker": rand_ticker,
            "exchange": rand_exchange,
            "risk_score": random.uniform(0.0, 1.0),
            "status": "EVALUATED"
        }
        mock_dispatch_return = {
            "status": "DISPATCHED",
            "channels": rand_channels
        }

        with patch("skills.market_sentiment_risk_hub.MarketSentimentRiskHub.evaluate_risk", return_value=mock_risk_return) as mock_eval, \
             patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts", return_value=mock_dispatch_return) as mock_disp:
            
            bridge = MarketSentimentRiskAlertBridge(
                token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage
            )
            result = bridge.bridge_evaluate_and_dispatch(
                ticker=rand_ticker,
                exchange=rand_exchange,
                news_snippet=rand_snippet,
                url=rand_url,
                severity_level=rand_severity,
                min_threshold=rand_threshold,
                channels=rand_channels
            )

            mock_eval.assert_called_once_with(rand_ticker, rand_exchange, rand_snippet)
            mock_disp.assert_called_once_with(
                symbol=rand_ticker,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage,
                severity_level=rand_severity,
                min_threshold=rand_threshold,
                channels=rand_channels
            )

            self.assertEqual(result["risk_data"], mock_risk_return)
            self.assertEqual(result["dispatch_result"], mock_dispatch_return)

    def test_bridge_process_stream(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(10000, 99999))
        rand_storage = f"{uuid.uuid4().hex}.db"
        rand_stream_source = f"stream_{uuid.uuid4().hex}"

        stream_items_mock = [
            {"id": uuid.uuid4().hex, "metric": random.randint(1, 100)},
            {"id": uuid.uuid4().hex, "metric": random.randint(101, 200)}
        ]
        dispatch_results_mock = [
            {"processed_id": stream_items_mock[0]["id"], "status": "OK"},
            {"processed_id": stream_items_mock[1]["id"], "status": "OK"}
        ]

        with patch("skills.market_sentiment_risk_hub.MarketSentimentRiskHub.process_stream", return_value=stream_items_mock) as mock_proc_stream, \
             patch("skills.market_portfolio_alert_dispatcher.process_stream_alert", side_effect=dispatch_results_mock) as mock_disp_stream:
            
            bridge = MarketSentimentRiskAlertBridge(
                token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage
            )
            results = bridge.bridge_process_stream(rand_stream_source)

            mock_proc_stream.assert_called_once_with(rand_stream_source)
            self.assertEqual(mock_disp_stream.call_count, len(stream_items_mock))
            self.assertEqual(results, dispatch_results_mock)

    def test_process_sentiment_risk_and_dispatch_alert_default_channels(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(1000, 9999))
        rand_storage = f"{uuid.uuid4().hex}.dat"
        rand_ticker = ''.join(random.choices(string.ascii_uppercase, k=3))
        rand_exchange = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_snippet = uuid.uuid4().hex
        rand_url = f"https://{uuid.uuid4().hex}.org"
        rand_severity = "HIGH"
        rand_threshold = 0.75

        mock_risk_data = {"score": 0.88, "ticker": rand_ticker}
        mock_disp_data = {"sent": True}

        with patch("skills.market_sentiment_risk_hub.MarketSentimentRiskHub.evaluate_risk", return_value=mock_risk_data) as mock_eval, \
             patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts", return_value=mock_disp_data) as mock_disp:
            
            res = process_sentiment_risk_and_dispatch_alert(
                ticker=rand_ticker,
                exchange=rand_exchange,
                news_snippet=rand_snippet,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage,
                severity_level=rand_severity,
                min_threshold=rand_threshold,
                channels=None
            )

            mock_eval.assert_called_once_with(rand_ticker, rand_exchange, rand_snippet)
            mock_disp.assert_called_once_with(
                symbol=rand_ticker,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage,
                severity_level=rand_severity,
                min_threshold=rand_threshold,
                channels=["telegram"]
            )

            self.assertEqual(res["risk_evaluation"], mock_risk_data)
            self.assertEqual(res["dispatch_status"], mock_disp_data)

    def test_process_sentiment_risk_and_dispatch_alert_custom_channels(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100, 999))
        rand_storage = f"{uuid.uuid4().hex}.log"
        rand_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_exchange = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_snippet = uuid.uuid4().hex
        rand_url = f"https://{uuid.uuid4().hex}.net"
        rand_severity = "LOW"
        rand_threshold = 0.2
        rand_channels = [uuid.uuid4().hex, uuid.uuid4().hex]

        mock_risk_data = {"score": 0.1, "alert": False}
        mock_disp_data = {"sent": False}

        with patch("skills.market_sentiment_risk_hub.MarketSentimentRiskHub.evaluate_risk", return_value=mock_risk_data) as mock_eval, \
             patch("skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts", return_value=mock_disp_data) as mock_disp:
            
            res = process_sentiment_risk_and_dispatch_alert(
                ticker=rand_ticker,
                exchange=rand_exchange,
                news_snippet=rand_snippet,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage,
                severity_level=rand_severity,
                min_threshold=rand_threshold,
                channels=rand_channels
            )

            mock_eval.assert_called_once_with(rand_ticker, rand_exchange, rand_snippet)
            mock_disp.assert_called_once_with(
                symbol=rand_ticker,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat_id,
                storage_file=rand_storage,
                severity_level=rand_severity,
                min_threshold=rand_threshold,
                channels=rand_channels
            )

            self.assertEqual(res["risk_evaluation"], mock_risk_data)
            self.assertEqual(res["dispatch_status"], mock_disp_data)

if __name__ == '__main__':
    unittest.main()