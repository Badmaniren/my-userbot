import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stream_alert_bridge import (
    process_stream_and_dispatch,
    evaluate_stream_anomaly_bridge,
    process_stream_and_dispatch_alert
)

class TestMarketPortfolioStreamAlertBridge(unittest.TestCase):

    def test_process_stream_and_dispatch_anomaly_true(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        rand_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"/tmp/{uuid.uuid4().hex}.json"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_threshold = round(random.uniform(1.0, 10.0), 2)
        rand_channels = [uuid.uuid4().hex, uuid.uuid4().hex]
        
        payload = {"data": uuid.uuid4().hex}
        output_path = f"/tmp/{uuid.uuid4().hex}.out"
        
        mock_stream_res = {"anomaly_detected": True, "details": uuid.uuid4().hex}
        mock_dispatch_res = {"status": "dispatched", "id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stream_alert_bridge.market_portfolio_realtime_stream_ingestor", return_value=mock_stream_res) as m_ingest, \
             patch("skills.market_portfolio_stream_alert_bridge.dispatch_portfolio_alerts", return_value=mock_dispatch_res) as m_dispatch:
            
            res = process_stream_and_dispatch(
                payload, output_path, rand_symbol, rand_url, rand_token,
                rand_chat, rand_storage, rand_severity, rand_threshold, rand_channels
            )
            
            m_ingest.assert_called_once_with(payload, output_path)
            m_dispatch.assert_called_once_with(
                rand_symbol, rand_url, rand_token, rand_chat,
                rand_storage, rand_severity, rand_threshold, rand_channels
            )
            
            self.assertEqual(res["stream_processing"], mock_stream_res)
            self.assertEqual(res["alert_dispatch_status"], mock_dispatch_res)
            self.assertTrue(res["alert_dispatched"])

    def test_process_stream_and_dispatch_anomaly_false(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        rand_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"/tmp/{uuid.uuid4().hex}.json"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_threshold = round(random.uniform(1.0, 10.0), 2)
        rand_channels = [uuid.uuid4().hex]
        
        payload = {"data": uuid.uuid4().hex}
        output_path = f"/tmp/{uuid.uuid4().hex}.out"
        
        mock_stream_res = {"anomaly_detected": False}

        with patch("skills.market_portfolio_stream_alert_bridge.market_portfolio_realtime_stream_ingestor", return_value=mock_stream_res) as m_ingest, \
             patch("skills.market_portfolio_stream_alert_bridge.dispatch_portfolio_alerts") as m_dispatch:
            
            res = process_stream_and_dispatch(
                payload, output_path, rand_symbol, rand_url, rand_token,
                rand_chat, rand_storage, rand_severity, rand_threshold, rand_channels
            )
            
            m_ingest.assert_called_once_with(payload, output_path)
            m_dispatch.assert_not_called()
            
            self.assertEqual(res["stream_processing"], mock_stream_res)
            self.assertIsNone(res["alert_dispatch_status"])
            self.assertFalse(res["alert_dispatched"])

    def test_evaluate_stream_anomaly_bridge_success(self):
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_source = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_template = f"ALERT_TMPL_{uuid.uuid4().hex[:4]}"
        rand_source_id = f"SRC_{uuid.uuid4().hex[:8]}"
        
        mock_start_result = {"source_id": rand_source_id, "status": "active"}

        with patch("skills.market_portfolio_stream_alert_bridge.start_new", return_value=mock_start_result) as m_start, \
             patch("skills.market_portfolio_stream_alert_bridge.send_telegram_notification") as m_send:
            
            res = evaluate_stream_anomaly_bridge(
                rand_context, rand_source, rand_token, rand_chat, rand_template
            )
            
            m_start.assert_called_once_with(rand_context, rand_source)
            expected_msg = f"{rand_template} - {rand_source_id}"
            m_send.assert_called_once_with(rand_token, rand_chat, expected_msg)
            self.assertEqual(res, mock_start_result)

    def test_evaluate_stream_anomaly_bridge_exception(self):
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_source = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_template = f"ALERT_TMPL_{uuid.uuid4().hex[:4]}"
        rand_err_msg = f"ERR_{uuid.uuid4().hex[:6]}"

        with patch("skills.market_portfolio_stream_alert_bridge.start_new", side_effect=Exception(rand_err_msg)) as m_start, \
             patch("skills.market_portfolio_stream_alert_bridge.send_telegram_notification") as m_send:
            
            res = evaluate_stream_anomaly_bridge(
                rand_context, rand_source, rand_token, rand_chat, rand_template
            )
            
            m_start.assert_called_once_with(rand_context, rand_source)
            expected_msg = f"{rand_template} - fallback_source_id"
            m_send.assert_called_once_with(rand_token, rand_chat, expected_msg)
            self.assertEqual(res["source_id"], "fallback_source_id")
            self.assertIn(rand_err_msg, res["error"])

    def test_process_stream_and_dispatch_alert_success(self):
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_source = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        rand_symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        rand_event_id = uuid.uuid4().hex
        payload = {"symbol": rand_symbol, "event_id": rand_event_id, "val": random.random()}
        output_path = f"/tmp/{uuid.uuid4().hex}.log"
        rand_url = f"https://{uuid.uuid4().hex[:8]}.org/hook"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"/tmp/{uuid.uuid4().hex}.db"
        rand_severity = "HIGH"
        rand_threshold = 5.0
        rand_channels = [uuid.uuid4().hex]
        
        mock_stream_res = {"anomaly_detected": True, "metrics": random.randint(1, 100)}
        mock_dispatch_res = {"dispatched": True, "code": 200}

        with patch("skills.market_portfolio_stream_alert_bridge.start_new") as m_start, \
             patch("skills.market_portfolio_stream_alert_bridge.market_portfolio_realtime_stream_ingestor", return_value=mock_stream_res) as m_ingest, \
             patch("skills.market_portfolio_stream_alert_bridge.dispatch_portfolio_alerts", return_value=mock_dispatch_res) as m_dispatch:
            
            res = process_stream_and_dispatch_alert(
                rand_context, rand_source, payload, output_path, rand_url,
                rand_token, rand_chat, rand_storage, rand_severity,
                rand_threshold, rand_channels
            )
            
            m_start.assert_called_once_with(rand_context, rand_source)
            m_ingest.assert_called_once_with(payload, output_path)
            m_dispatch.assert_called_once_with(
                rand_symbol, rand_url, rand_token, rand_chat,
                rand_storage, rand_severity, rand_threshold, rand_channels
            )
            
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["event_id"], rand_event_id)
            self.assertEqual(res["stream_processing"], mock_stream_res)
            self.assertEqual(res["alert_dispatch_status"], mock_dispatch_res)
            self.assertTrue(res["dispatched"])

    def test_process_stream_and_dispatch_alert_start_exception(self):
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_source = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        rand_symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        payload = {"symbol": rand_symbol}
        output_path = f"/tmp/{uuid.uuid4().hex}.log"
        rand_url = f"https://{uuid.uuid4().hex[:8]}.org/hook"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"/tmp/{uuid.uuid4().hex}.db"
        rand_severity = "LOW"
        rand_threshold = 1.0
        rand_channels = []

        with patch("skills.market_portfolio_stream_alert_bridge.start_new", side_effect=ValueError(uuid.uuid4().hex)) as m_start, \
             patch("skills.market_portfolio_stream_alert_bridge.market_portfolio_realtime_stream_ingestor") as m_ingest:
            
            with self.assertRaises(ValueError):
                process_stream_and_dispatch_alert(
                    rand_context, rand_source, payload, output_path, rand_url,
                    rand_token, rand_chat, rand_storage, rand_severity,
                    rand_threshold, rand_channels
                )
            
            m_start.assert_called_once_with(rand_context, rand_source)
            m_ingest.assert_not_called()