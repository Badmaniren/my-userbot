import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_sentiment_digest import (
    generate_sentiment_portfolio_digest,
    MarketSentimentDigestEngine
)
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_portfolio_digest import PortfolioDigestManager


class TestMarketSentimentDigestArchitect(unittest.TestCase):

    def setUp(self):
        self.random_symbol = f"{''.join(random.choices(string.ascii_uppercase, k=4))}"
        self.random_url = f"https://{uuid.uuid4().hex}.com/api/{uuid.uuid4().hex}"
        self.random_token = f"{random.randint(100000, 999999)}:AAF{uuid.uuid4().hex[:16]}"
        self.random_chat_id = str(random.randint(-999999999, -100000000))
        self.random_storage = f"storage_{uuid.uuid4().hex}.db"

    def test_composition_imports_and_instantiation(self):
        analyzer = MarketNewsSentimentAnalyzer()
        self.assertIsInstance(analyzer, MarketNewsSentimentAnalyzer)

        manager = PortfolioDigestManager(self.random_storage)
        self.assertIsInstance(manager, PortfolioDigestManager)

        engine = MarketSentimentDigestEngine(self.random_storage)
        self.assertIsNotNone(engine)
        self.assertTrue(hasattr(engine, "compile_sentiment_digest"))

    def test_generate_sentiment_portfolio_digest_composition_flow(self):
        expected_sentiment_result = {
            "entity": self.random_symbol,
            "sentiment_score": round(random.uniform(-1.0, 1.0), 4),
            "payload_id": uuid.uuid4().hex
        }
        expected_digest_data = {
            "symbol": self.random_symbol,
            "status": "compiled",
            "hash": uuid.uuid4().hex
        }

        with patch("skills.market_sentiment_digest.MarketNewsSentimentAnalyzer") as MockAnalyzerClass, \
             patch("skills.market_sentiment_digest.PortfolioDigestManager") as MockManagerClass:
            
            mock_analyzer_instance = MockAnalyzerClass.return_value
            mock_analyzer_instance.analyze.return_value = expected_sentiment_result

            mock_manager_instance = MockManagerClass.return_value
            mock_manager_instance.compile_digest.return_value = expected_digest_data

            result = generate_sentiment_portfolio_digest(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )

            MockAnalyzerClass.assert_called_once()
            MockManagerClass.assert_called_once_with(self.random_storage)
            mock_analyzer_instance.analyze.assert_called_once()
            mock_manager_instance.compile_digest.assert_called_once_with(self.random_symbol, self.random_url)
            mock_manager_instance.render_and_send.assert_called_once_with(
                self.random_symbol, self.random_token, self.random_chat_id
            )

            self.assertIn("sentiment", result)
            self.assertIn("digest", result)
            self.assertEqual(result["sentiment"]["payload_id"], expected_sentiment_result["payload_id"])
            self.assertEqual(result["digest"]["hash"], expected_digest_data["hash"])

    def test_market_sentiment_digest_engine_methods(self):
        random_news_snippet = f"Breaking news for {self.random_symbol}: revenue increased by {random.randint(10, 99)}%."
        mock_stream_data = [
            {"id": uuid.uuid4().hex, "text": random_news_snippet},
            {"id": uuid.uuid4().hex, "text": f"Bearish sentiment detected on {self.random_symbol}"}
        ]

        engine = MarketSentimentDigestEngine(self.random_storage)

        with patch.object(MarketNewsSentimentAnalyzer, "batch_analyze_stream") as mock_batch, \
             patch.object(PortfolioDigestManager, "compile_digest") as mock_compile:

            mock_batch.return_value = mock_stream_data
            mock_compile.return_value = {"symbol": self.random_symbol, "metrics": random.randint(100, 500)}

            stream_filename = f"stream_{uuid.uuid4().hex}.json"
            analysis_result = engine.process_sentiment_stream_and_digest(
                filename=stream_filename,
                symbol=self.random_symbol,
                url=self.random_url
            )

            mock_batch.assert_called_once_with(stream_filename)
            mock_compile.assert_called_once_with(self.random_symbol, self.random_url)

            self.assertIn("stream_analysis", analysis_result)
            self.assertEqual(len(analysis_result["stream_analysis"]), 2)
            self.assertEqual(analysis_result["stream_analysis"][0]["id"], mock_stream_data[0]["id"])

    def test_io_stream_handling_in_digest_pipeline(self):
        garbage_bytes = f"garbage_stream_{uuid.uuid4().hex}".encode('utf-8')
        fake_io = io.BytesIO(garbage_bytes)

        with patch("skills.market_sentiment_digest.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = fake_io.read()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            engine = MarketSentimentDigestEngine(self.random_storage)
            fetched_content = engine.fetch_raw_feed(self.random_url)

            mock_get.assert_called_once_with(self.random_url, timeout=unittest.mock.ANY)
            self.assertEqual(fetched_content, garbage_bytes)


if __name__ == "__main__":
    unittest.main()