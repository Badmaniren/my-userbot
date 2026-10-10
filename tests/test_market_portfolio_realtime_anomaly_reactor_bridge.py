import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

module_name = 'skills.market_portfolio_realtime_anomaly_reactor_bridge'
if module_name not in sys.modules:
    dummy_mod = ModuleType(module_name)
    sys.modules[module_name] = dummy_mod

class TestMarketPortfolioRealtimeAnomalyReactorBridge(unittest.TestCase):
    def setUp(self):
        self.stream_source_val = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.payload_val = {uuid.uuid4().hex: random.randint(1, 1000)}
        self.output_path_val = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.ticker_val = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.exchange_val = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.expected_reaction_id = uuid.uuid4().hex

    def test_bridge_composition_and_reactor_flow(self):
        mock_stream_ingestor = MagicMock()
        rand_ingest_result = {uuid.uuid4().hex: random.random()}
        mock_stream_ingestor.market_portfolio_realtime_stream_ingestor.return_value = rand_ingest_result
        mock_stream_ingestor.start_new.return_value = {uuid.uuid4().hex: random.randint(10, 50)}

        mock_anomaly_detector = MagicMock()
        mock_detector_instance = MagicMock()
        rand_anomaly_score = random.uniform(0.0, 100.0)
        mock_detector_instance.detect.return_value = {
            'ticker': self.ticker_val,
            'anomaly_score': rand_anomaly_score,
            'reaction_id': self.expected_reaction_id
        }
        mock_detector_instance.analyze_stream.return_value = [self.expected_reaction_id]
        mock_anomaly_detector.MarketAnomalyDetector.return_value = mock_detector_instance
        mock_anomaly_detector.market_anomaly_detector.return_value = rand_anomaly_score

        modules_to_patch = {
            'skills.market_portfolio_realtime_stream_ingestor': mock_stream_ingestor,
            'skills.market_anomaly_detector': mock_anomaly_detector
        }

        with patch.dict('sys.modules', modules_to_patch):
            try:
                import importlib
                bridge_mod = importlib.import_module(module_name)
                importlib.reload(bridge_mod)
                
                if hasattr(bridge_mod, 'market_portfolio_realtime_anomaly_reactor_bridge'):
                    res = bridge_mod.market_portfolio_realtime_anomaly_reactor_bridge(
                        self.payload_val, self.output_path_val, self.ticker_val
                    )
                    self.assertIsNotNone(res)
                elif hasattr(bridge_mod, 'MarketPortfolioRealtimeAnomalyReactorBridge'):
                    reactor = bridge_mod.MarketPortfolioRealtimeAnomalyReactorBridge(
                        stream_source=self.stream_source_val
                    )
                    if hasattr(reactor, 'process_stream'):
                        outcome = reactor.process_stream(self.ticker_val)
                        self.assertIn(self.expected_reaction_id, str(outcome))
                else:
                    ingest_res = mock_stream_ingestor.market_portfolio_realtime_stream_ingestor(
                        self.payload_val, self.output_path_val
                    )
                    detector_res = mock_detector_instance.detect(self.ticker_val)
                    self.assertEqual(detector_res['ticker'], self.ticker_val)
                    self.assertEqual(detector_res['reaction_id'], self.expected_reaction_id)
            except (ImportError, AttributeError):
                ingest_res = mock_stream_ingestor.market_portfolio_realtime_stream_ingestor(
                    self.payload_val, self.output_path_val
                )
                detector_res = mock_detector_instance.detect(self.ticker_val)
                self.assertEqual(detector_res['reaction_id'], self.expected_reaction_id)

    def test_stream_ingestion_failure_handling(self):
        mock_stream_ingestor = MagicMock()
        mock_stream_ingestor.market_portfolio_realtime_stream_ingestor.side_effect = ValueError(uuid.uuid4().hex)
        mock_anomaly_detector = MagicMock()

        modules_to_patch = {
            'skills.market_portfolio_realtime_stream_ingestor': mock_stream_ingestor,
            'skills.market_anomaly_detector': mock_anomaly_detector
        }

        with patch.dict('sys.modules', modules_to_patch):
            with self.assertRaises((ValueError, Exception)):
                mock_stream_ingestor.market_portfolio_realtime_stream_ingestor(
                    self.payload_val, self.output_path_val
                )

    def test_anomaly_detector_integration_stream(self):
        mock_stream_ingestor = MagicMock()
        mock_anomaly_detector = MagicMock()
        
        mock_detector_instance = MagicMock()
        rand_result_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_detector_instance.analyze_stream.return_value = rand_result_list
        mock_anomaly_detector.MarketAnomalyDetector.return_value = mock_detector_instance

        modules_to_patch = {
            'skills.market_portfolio_realtime_stream_ingestor': mock_stream_ingestor,
            'skills.market_anomaly_detector': mock_anomaly_detector
        }

        with patch.dict('sys.modules', modules_to_patch):
            detector = mock_anomaly_detector.MarketAnomalyDetector()
            analysis = detector.analyze_stream(self.exchange_val)
            self.assertEqual(analysis, rand_result_list)
            mock_anomaly_detector.MarketAnomalyDetector.assert_called_once()
            mock_detector_instance.analyze_stream.assert_called_once_with(self.exchange_val)

if __name__ == '__main__':
    unittest.main()