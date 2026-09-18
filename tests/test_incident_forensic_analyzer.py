import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.incident_forensic_analyzer import start_new, incident_forensic_analyzer

class TestIncidentForensicAnalyzer(unittest.TestCase):

    def test_start_new_empty_config(self):
        rnd_metric = random.randint(100, 999)
        rnd_id = uuid.uuid4().hex
        
        with patch("skills.incident_forensic_analyzer.system_health_telemetry_collector") as mock_collector, \
             patch("skills.incident_forensic_analyzer.telemetry_streamer") as mock_streamer, \
             patch("skills.incident_forensic_analyzer.incident_aggregator") as mock_aggregator:
            
            mock_stream_inst = MagicMock()
            mock_stream_inst.read.return_value = io.BytesIO(uuid.uuid4().bytes)
            mock_streamer.return_value = mock_stream_inst

            config_data = {}
            res = start_new(config_data)
            
            mock_collector.collect.assert_called_once()
            self.assertIsInstance(res, str)

    def test_start_new_corrupted_stream(self):
        rnd_id = uuid.uuid4().hex
        rnd_result = uuid.uuid4().hex

        with patch("skills.incident_forensic_analyzer.error_recovery_hub") as mock_recovery:
            mock_recovery.handle_failure.return_value = rnd_result
            
            config_data = {
                "corrupted_stream": True,
                "incident_id": rnd_id
            }
            res = start_new(config_data)
            
            mock_recovery.handle_failure.assert_called_once_with(rnd_id)
            self.assertEqual(res, rnd_result)

    def test_start_new_severity_level(self):
        rnd_severity = uuid.uuid4().hex
        rnd_result = {"status": uuid.uuid4().hex}

        with patch("skills.incident_forensic_analyzer.incident_severity_evaluator") as mock_evaluator:
            mock_evaluator.evaluate.return_value = rnd_result
            
            config_data = {
                "severity_level": rnd_severity
            }
            res = start_new(config_data)
            
            mock_evaluator.evaluate.assert_called_once_with(config_data)
            self.assertEqual(res, rnd_result)

    def test_start_new_financial_index(self):
        rnd_index = random.uniform(1.0, 100.0)
        rnd_result = {"impact": uuid.uuid4().hex}

        with patch("skills.incident_forensic_analyzer.incident_severity_evaluator") as mock_evaluator:
            mock_evaluator.evaluate.return_value = rnd_result
            
            config_data = {
                "financial_index": rnd_index
            }
            res = start_new(config_data)
            
            mock_evaluator.evaluate.assert_called_once_with(config_data)
            self.assertEqual(res, rnd_result)

    def test_start_new_anomaly_signature(self):
        rnd_sig = uuid.uuid4().hex
        rnd_result = {"detected": True}

        with patch("skills.incident_forensic_analyzer.telemetry_anomaly_evaluator_core") as mock_anomaly:
            mock_anomaly.detect.return_value = rnd_result
            
            config_data = {
                "anomaly_signature": rnd_sig
            }
            res = start_new(config_data)
            
            mock_anomaly.detect.assert_called_once_with(config_data)
            self.assertEqual(res, rnd_result)

    def test_start_new_standard_flow(self):
        rnd_id = uuid.uuid4().hex
        rnd_log_path = f"/tmp/{uuid.uuid4().hex}.log"
        rnd_source = uuid.uuid4().hex

        with patch("skills.incident_forensic_analyzer.telemetry_streamer") as mock_streamer, \
             patch("skills.incident_forensic_analyzer.incident_aggregator") as mock_aggregator:
            
            mock_stream_inst = MagicMock()
            mock_streamer.return_value = mock_stream_inst

            config_data = {
                "incident_id": rnd_id,
                "log_path": rnd_log_path,
                "telemetry_source": rnd_source
            }
            res = start_new(config_data)
            
            mock_streamer.assert_called_once_with(rnd_source)
            mock_stream_inst.read.assert_called_once()
            self.assertIn(rnd_id, res)
            self.assertIn(rnd_log_path, res)

    def test_incident_forensic_analyzer_basic(self):
        rnd_id = uuid.uuid4().hex
        rnd_metric = random.randint(1000, 9999)
        rnd_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        payload = {
            "telemetry_ref": {
                "metric_val": rnd_metric
            },
            "extra": uuid.uuid4().hex
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("os.makedirs") as mock_mkdirs:
            
            res = incident_forensic_analyzer(rnd_id, payload, rnd_path)
            
            mock_mkdirs.assert_called_once()
            mock_file.assert_called_once_with(rnd_path, "w", encoding="utf-8")
            self.assertEqual(res["target_incident_id"], rnd_id)
            self.assertEqual(res["metric_val"], rnd_metric)
            self.assertEqual(res["payload"], payload)