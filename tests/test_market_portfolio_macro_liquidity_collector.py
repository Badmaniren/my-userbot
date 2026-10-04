import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from skills.market_portfolio_macro_liquidity_collector import MarketPortfolioMacroLiquidityCollector


class TestMarketPortfolioMacroLiquidityCollector(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.news_analyzer = MagicMock()
        self.parser = MagicMock()

        self.collector = MarketPortfolioMacroLiquidityCollector(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_news_sentiment_analyzer=self.news_analyzer,
            market_parser=self.parser
        )

    def test_collect_macro_liquidity_metrics_success(self):
        rand_rate = round(random.uniform(0.01, 5.50), 4)
        rand_m2 = random.randint(1000000, 999999999)
        rand_repo = round(random.uniform(100.0, 5000.0), 2)
        rand_url = f"https://{uuid.uuid4().hex}.com/api/macro"
        rand_payload = f"data_{uuid.uuid4().hex}"

        self.extractor_1.fetch.return_value = {"central_bank_rate": rand_rate}
        self.extractor_2.fetch.return_value = {"m2_money_supply": rand_m2}
        self.extractor_3.fetch.return_value = {"reverse_repo": rand_repo}
        self.parser.parse.return_value = {"status": "parsed", "payload": rand_payload}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = f'{{"metric_id": "{rand_payload}"}}'.encode('utf-8')
        mock_response.json.return_value = {"metric_id": rand_payload}

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.collector.collect_and_store(rand_url)

            mock_get.assert_called_once_with(rand_url, timeout=unittest.mock.ANY)
            self.assertIn("rate", result)
            self.assertEqual(result["rate"], rand_rate)
            self.assertEqual(result["m2"], rand_m2)
            self.assertEqual(result["reverse_repo"], rand_repo)
            self.db_storage.save.assert_called()

    def test_collect_macro_liquidity_network_failure(self):
        rand_url = f"https://{uuid.uuid4().hex}.org/failure"

        with patch('requests.get', side_effect=requests.exceptions.Timeout) as mock_get:
            with self.assertRaises(Exception):
                self.collector.collect_and_store(rand_url)
            mock_get.assert_called_once()
            self.db_storage.save.assert_not_called()

    def test_stream_parser_data_handling(self):
        rand_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        stream_data = io.BytesIO(rand_string.encode('utf-8'))

        rand_id = str(uuid.uuid4())
        self.parser.parse_stream.return_value = {"id": rand_id, "content": rand_string}

        result = self.collector.process_stream(stream_data)

        self.assertEqual(result["id"], rand_id)
        self.assertEqual(result["content"], rand_string)
        self.parser.parse_stream.assert_called_once_with(stream_data)

    def test_anomaly_detection_trigger(self):
        rand_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        rand_anomaly_score = round(random.uniform(75.0, 99.9), 2)

        self.anomaly_detector.evaluate.return_value = {
            "is_anomaly": True,
            "score": rand_anomaly_score,
            "metric": rand_metric_name
        }

        eval_result = self.collector.check_liquidity_anomaly(rand_metric_name, rand_anomaly_score)

        self.assertTrue(eval_result["is_anomaly"])
        self.assertEqual(eval_result["score"], rand_anomaly_score)
        self.assertEqual(eval_result["metric"], rand_metric_name)
        self.anomaly_detector.evaluate.assert_called_once_with(rand_metric_name, rand_anomaly_score)