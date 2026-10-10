import unittest
from unittest.mock import patch
import io
import json
import uuid
import random
from skills.market_portfolio_realtime_anomaly_reactor import (
    MarketPortfolioRealtimeAnomalyReactor,
    market_portfolio_realtime_anomaly_reactor_main,
    process_realtime_anomaly_event,
    reactor_main_pipeline
)

class TestMarketPortfolioRealtimeAnomalyReactorIntegration(unittest.TestCase):

    def test_realtime_anomaly_reactor_composition(self):
        rand_session = uuid.uuid4().hex
        rand_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        rand_exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"
        rand_price = round(random.uniform(10.0, 1000.0), 2)
        
        context = {
            "session_id": rand_session,
            "db_storage": f"db_{uuid.uuid4().hex[:8]}"
        }
        
        mock_ingest_result = {
            "status": "ingested",
            "session_id": rand_session,
            "bytes_processed": random.randint(100, 5000)
        }
        
        mock_detection_result = {
            "is_anomaly": True,
            "score": round(random.uniform(0.8, 0.99), 4),
            "ticker": rand_ticker
        }
        
        with patch("skills.market_portfolio_realtime_stream_ingestor.start_new", return_value=mock_ingest_result) as mock_start_new, \
             patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect", return_value=mock_detection_result) as mock_detect:
            
            reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=rand_exchange)
            result = reactor.process_stream_tick(context, rand_ticker)
            
            mock_start_new.assert_called_once_with(context, rand_exchange)
            mock_detect.assert_called_once_with(rand_ticker)
            
            self.assertTrue(result["anomaly_detected"])
            self.assertEqual(result["ticker"], rand_ticker)
            self.assertEqual(result["ingest_result"], mock_ingest_result)
            self.assertEqual(result["detection"], mock_detection_result)

    def test_evaluate_exchange_feed(self):
        rand_output = f"{uuid.uuid4().hex}.json"
        rand_exchange = f"EXCH_{uuid.uuid4().hex[:4]}"
        rand_ticker = f"TICK_{uuid.uuid4().hex[:4]}"
        
        payload = {
            "ticker": rand_ticker,
            "price": random.randint(50, 500)
        }
        
        mock_audit = {
            "audit_id": uuid.uuid4().hex,
            "status": "audited"
        }
        
        mock_anomalies = [
            {"anomaly_id": uuid.uuid4().hex, "severity": "HIGH"}
        ]
        
        with patch("skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor", return_value=mock_audit) as mock_ingest_audit, \
             patch("skills.market_anomaly_detector.MarketAnomalyDetector.analyze_stream", return_value=mock_anomalies) as mock_analyze:
             
            reactor = MarketPortfolioRealtimeAnomalyReactor()
            res = reactor.evaluate_exchange_feed(payload, rand_output, rand_exchange)
            
            mock_ingest_audit.assert_called_once_with(payload, rand_output)
            mock_analyze.assert_called_once_with(rand_exchange)
            
            self.assertEqual(res["exchange"], rand_exchange)
            self.assertEqual(res["anomalies"], mock_anomalies)
            self.assertEqual(res["ingest_audit"], mock_audit)

    def test_process_raw_bytes_stream(self):
        rand_data = uuid.uuid4().bytes + uuid.uuid4().bytes
        bio = io.BytesIO(rand_data)
        
        reactor = MarketPortfolioRealtimeAnomalyReactor()
        read_bytes = reactor._process_raw_bytes_stream(bio)
        
        self.assertEqual(read_bytes, rand_data)

    def test_process_realtime_anomaly_event_with_detection(self):
        rand_ticker = f"T_{uuid.uuid4().hex[:5]}"
        rand_exchange = f"E_{uuid.uuid4().hex[:5]}"
        rand_output = f"out_{uuid.uuid4().hex}.json"
        
        payload = {
            "ticker": rand_ticker,
            "exchange": rand_exchange,
            "value": random.random()
        }
        
        mock_ingest = {"status": "ok"}
        mock_detection = {"is_anomaly": True, "info": uuid.uuid4().hex}
        
        with patch("skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor", return_value=mock_ingest) as mock_ingest_fn, \
             patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect", return_value=mock_detection) as mock_detect_fn:
             
            res = process_realtime_anomaly_event(payload, rand_output)
            
            mock_ingest_fn.assert_called_once_with(payload, rand_output)
            mock_detect_fn.assert_called_once_with(rand_ticker)
            
            self.assertEqual(res["status"], "success")
            self.assertTrue(res["anomaly_detected"])
            self.assertEqual(res["ticker"], rand_ticker)
            self.assertEqual(res["ingest_result"], mock_ingest)
            self.assertEqual(res["detection"], mock_detection)

    def test_process_realtime_anomaly_event_fallback(self):
        rand_ticker = f"T_{uuid.uuid4().hex[:5]}"
        rand_exchange = f"E_{uuid.uuid4().hex[:5]}"
        rand_output = f"out_{uuid.uuid4().hex}.json"
        
        payload = {
            "ticker": rand_ticker,
            "exchange": rand_exchange
        }
        
        mock_ingest = {"status": "ok"}
        mock_stream_anomalies = [{"id": uuid.uuid4().hex}]
        
        with patch("skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor", return_value=mock_ingest), \
             patch("skills.market_anomaly_detector.MarketAnomalyDetector.detect", return_value=None), \
             patch("skills.market_anomaly_detector.MarketAnomalyDetector.analyze_stream", return_value=mock_stream_anomalies) as mock_analyze:
             
            res = process_realtime_anomaly_event(payload, rand_output)
            
            mock_analyze.assert_called_once_with(rand_exchange)
            self.assertTrue(res["anomaly_detected"])
            self.assertEqual(res["detection"], mock_stream_anomalies)

    def test_reactor_main_pipeline(self):
        rand_ticker = f"TK_{uuid.uuid4().hex[:4]}"
        rand_exchange = f"EX_{uuid.uuid4().hex[:4]}"
        rand_output = f"file_{uuid.uuid4().hex}.json"
        
        stream_source = {
            "ticker": rand_ticker,
            "exchange": rand_exchange,
            "price": round(random.uniform(1.0, 100.0), 2)
        }
        
        mock_ingest = {"ingested": True}
        mock_anomalies = []
        
        with patch("skills.market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor", return_value=mock_ingest), \
             patch("skills.market_anomaly_detector.MarketAnomalyDetector.analyze_stream", return_value=mock_anomalies), \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file_open:
             
            res = reactor_main_pipeline(stream_source, rand_output)
            
            mock_file_open.assert_called_once_with(rand_output, "w", encoding="utf-8")
            self.assertEqual(res["status"], "pipeline_completed")
            self.assertEqual(res["ingest"], mock_ingest)
            self.assertEqual(res["anomalies"], mock_anomalies)

    def test_market_portfolio_realtime_anomaly_reactor_main(self):
        rand_arg1 = uuid.uuid4().hex
        rand_arg2 = f"T_{uuid.uuid4().hex[:4]}"
        
        with patch("sys.argv", ["script.py", rand_arg1, rand_arg2]), \
             patch("skills.market_portfolio_realtime_anomaly_reactor.MarketPortfolioRealtimeAnomalyReactor.process_stream_tick") as mock_process:
             
            market_portfolio_realtime_anomaly_reactor_main()
            mock_process.assert_called_once()
            args, _ = mock_process.call_args
            self.assertEqual(args[1], rand_arg2)


if __name__ == "__main__":
    unittest.main()