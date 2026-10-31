import unittest
from unittest.mock import patch, mock_open
import os
import json
import uuid
import random
import io
from skills.anomaly_pipeline import AnomalyLogger, AnomalyAuditHub, start_new, start_pipeline, ExtractorTool, GitInspector

class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_log_name = f"{uuid.uuid4().hex}.log"
        self.rand_repo_path = f"/path/to/{uuid.uuid4().hex}"

    def test_anomaly_logger_initialization_and_clearing(self):
        logger = AnomalyLogger(log_path=self.rand_log_name)
        self.assertEqual(logger.log_path, self.rand_log_name)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open()) as mocked_file:
            logger.clear_logs()
            mocked_file.assert_called_with(self.rand_log_name, "w", encoding="utf-8")
            mocked_file().write.assert_called_once_with("")

    def test_anomaly_logger_log_and_get(self):
        logger = AnomalyLogger(log_path=self.rand_log_name)
        source = uuid.uuid4().hex
        severity = random.randint(1, 10)
        details = uuid.uuid4().hex
        telemetry = {"cpu": random.random()}

        mock_data = json.dumps({
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry
        }) + "\n"

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)) as mocked_file:
            
            logger.log_anomaly(source, severity, details, telemetry)
            mocked_file.assert_called()

            anomalies = logger.get_anomalies()
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0]["source"], source)
            self.assertEqual(anomalies[0]["severity"], severity)
            self.assertEqual(anomalies[0]["details"], details)
            self.assertEqual(anomalies[0]["telemetry"], telemetry)

    def test_anomaly_logger_get_structured_report(self):
        logger = AnomalyLogger(log_path=self.rand_log_name)
        with patch.object(logger, "get_anomalies", return_value=[{"id": uuid.uuid4().hex}]):
            report = logger.get_structured_report()
            self.assertIn("anomalies", report)
            self.assertEqual(len(report["anomalies"]), 1)

    def test_anomaly_audit_hub_workflow(self):
        threshold = random.randint(50, 100)
        hub = AnomalyAuditHub(repo_path=self.rand_repo_path, log_path=self.rand_log_name, threshold=threshold)
        
        source = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        details = uuid.uuid4().hex
        telemetry_snapshot = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(hub.logger, "log_anomaly") as mock_log:
            hub.log_anomaly(source, severity, details, telemetry_snapshot)
            mock_log.assert_called_once_with(source, severity, details, telemetry_snapshot)

        metric_name = uuid.uuid4().hex
        metric_value = random.randint(0, 200)
        res = hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(res)
        self.assertIn({"name": metric_name, "value": metric_value}, hub.metrics)

        self.assertEqual(hub.correlate_metric(threshold + 5), True)
        self.assertEqual(hub.correlate_metric(threshold - 5), False)

        with patch.object(hub.logger, "get_anomalies", return_value=[]):
            final_report = hub.generate_final_report()
            self.assertIn("report_id", final_report)
            self.assertIn("metrics", final_report)
            self.assertIn("anomalies", final_report)

    def test_start_new_and_pipeline(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        input_data = {rand_key: rand_val}

        res_new = start_new(input_data)
        self.assertTrue(res_new.get("filtered"))
        self.assertEqual(res_new[rand_key], rand_val)

        res_new_non_dict = start_new(rand_val)
        self.assertTrue(res_new_non_dict.get("filtered"))
        self.assertEqual(res_new_non_dict["data"], rand_val)

        res_pipeline = start_pipeline(input_data)
        self.assertTrue(res_pipeline.get("filtered"))
        self.assertEqual(res_pipeline[rand_key], rand_val)

        res_pipeline_empty = start_pipeline(None)
        self.assertTrue(res_pipeline_empty.get("filtered"))

    def test_extractor_tool(self):
        extractor = ExtractorTool()
        key1, val1 = uuid.uuid4().hex, uuid.uuid4().hex
        key2, val2 = uuid.uuid4().hex, uuid.uuid4().hex
        tag_string = f'{key1}="{val1}" {key2}="{val2}"'

        parsed = extractor.parse_attributes(tag_string)
        self.assertEqual(parsed.get(key1), val1)
        self.assertEqual(parsed.get(key2), val2)

        markup_str = uuid.uuid4().hex
        extracted = extractor.extract(markup_str)
        self.assertEqual(extracted["markup"], markup_str)
        self.assertTrue(extracted["parsed"])

    def test_git_inspector(self):
        inspector = GitInspector(repo_path=self.rand_repo_path)
        self.assertEqual(inspector.repo_path, self.rand_repo_path)

        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)
        self.assertIn("commit", history[0])

        commit_hash = uuid.uuid4().hex
        filepath = uuid.uuid4().hex
        content = inspector.read_file_at_commit(commit_hash, filepath)
        self.assertIsInstance(content, bytes)

        analysis = inspector.analyze_repository()
        self.assertIn("status", analysis)

    def test_logger_io_mocking(self):
        logger = AnomalyLogger(log_path=self.rand_log_name)
        source = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        details = uuid.uuid4().hex
        telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}

        record = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry
        }
        file_content = json.dumps(record) + "\n"

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=file_content)) as mocked_file:
            anomalies = logger.get_anomalies()
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0]["source"], source)
            self.assertEqual(anomalies[0]["severity"], severity)
            self.assertEqual(anomalies[0]["details"], details)
            self.assertEqual(anomalies[0]["telemetry"], telemetry)

if __name__ == "__main__":
    unittest.main()