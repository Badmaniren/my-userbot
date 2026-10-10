import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.market_portfolio_realtime_anomaly_reactor import (
    MarketPortfolioRealtimeAnomalyReactor,
    market_portfolio_realtime_anomaly_reactor_main
)

class TestMarketPortfolioRealtimeAnomalyReactor(unittest.TestCase):

    def setUp(self):
        self.stream_source_rand = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.exchange_rand = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.ticker_rand = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.output_path_rand = f"/{''.join(random.choices(string.ascii_lowercase, k=8))}/output.json"
        self.context_rand = {
            "session_id": str(uuid.uuid4()),
            "priority": random.choice(["HIGH", "CRITICAL", "NORMAL"])
        }
        self.payload_rand = {
            "event_id": str(uuid.uuid4()),
            "price": random.uniform(10.0, 1500.0),
            "volume": random.randint(100, 50000)
        }

    @patch('skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector')
    def test_reactor_detects_and_processes_anomaly(self, mock_detector_cls, mock_ingestor):
        mock_stream_result = {
            "status": "success",
            "stream_id": str(uuid.uuid4()),
            "data": self.payload_rand
        }
        mock_ingestor.start_new.return_value = mock_stream_result

        mock_detector_instance = mock_detector_cls.return_value
        anomaly_flag = random.choice([True, False])
        mock_detector_instance.detect.return_value = {
            "is_anomaly": anomaly_flag,
            "ticker": self.ticker_rand,
            "severity": random.choice(["LOW", "HIGH"])
        }

        reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=self.stream_source_rand)
        result = reactor.process_stream_tick(self.context_rand, self.ticker_rand)

        self.assertIn("anomaly_detected", result)
        self.assertEqual(result["anomaly_detected"], anomaly_flag)
        self.assertEqual(result["ticker"], self.ticker_rand)
        mock_ingestor.start_new.assert_called_once_with(self.context_rand, self.stream_source_rand)
        mock_detector_instance.detect.assert_called_once_with(self.ticker_rand)

    @patch('skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector')
    def test_reactor_analyze_exchange_stream(self, mock_detector_cls, mock_ingestor_mod):
        mock_ingestor_func = mock_ingestor_mod.market_portfolio_realtime_stream_ingestor
        ingest_res = {
            "audit_status": "verified",
            "records_processed": random.randint(10, 1000)
        }
        mock_ingestor_func.return_value = ingest_res

        mock_detector_instance = mock_detector_cls.return_value
        analyzed_anomalies = [
            {"symbol": f"SYM_{random.randint(1, 100)}", "score": random.random()}
        ]
        mock_detector_instance.analyze_stream.return_value = analyzed_anomalies

        reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=self.stream_source_rand)
        res = reactor.evaluate_exchange_feed(self.payload_rand, self.output_path_rand, self.exchange_rand)

        self.assertEqual(res["exchange"], self.exchange_rand)
        self.assertEqual(res["anomalies"], analyzed_anomalies)
        self.assertEqual(res["ingest_audit"], ingest_res)
        mock_ingestor_func.assert_called_once_with(self.payload_rand, self.output_path_rand)
        mock_detector_instance.analyze_stream.assert_called_once_with(self.exchange_rand)

    @patch('skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor')
    def test_reactor_raises_no_silent_exceptions(self, mock_ingestor):
        mock_ingestor.start_new.side_effect = ConnectionError(f"Stream failure {uuid.uuid4().hex}")

        reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=self.stream_source_rand)
        
        with self.assertRaises(ConnectionError):
            reactor.process_stream_tick(self.context_rand, self.ticker_rand)

    @patch('skills.market_portfolio_realtime_anomaly_reactor.market_portfolio_realtime_stream_ingestor')
    @patch('skills.market_portfolio_realtime_anomaly_reactor.MarketAnomalyDetector')
    def test_main_entrypoint(self, mock_detector_cls, mock_ingestor):
        mock_stream_result = {
            "status": "active",
            "stream_id": str(uuid.uuid4())
        }
        mock_ingestor.start_new.return_value = mock_stream_result

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect.return_value = {
            "is_anomaly": True,
            "ticker": self.ticker_rand
        }

        with patch('sys.argv', ['script.py', self.stream_source_rand, self.ticker_rand]):
            output = market_portfolio_realtime_anomaly_reactor_main()

        self.assertIsInstance(output, dict)
        self.assertEqual(output["ticker"], self.ticker_rand)
        self.assertTrue(output["anomaly_detected"])

    def test_io_stream_handling(self):
        random_bytes = f"data_{uuid.uuid4().hex}".encode('utf-8')
        bio = io.BytesIO(random_bytes)
        
        reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=self.stream_source_rand)
        consumed_data = reactor._process_raw_bytes_stream(bio)

        self.assertEqual(consumed_data, random_bytes)

if __name__ == '__main__':
    unittest.main()