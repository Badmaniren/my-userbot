import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.anomaly_pipeline import (
    AnomalyLogger,
    AnomalyAuditHub,
    start_new,
    start_pipeline,
    ExtractorTool,
    GitInspector
)

class TestAnomalyPipelineInquisition(unittest.TestCase):

    def setUp(self):
        self.random_log_name = f"log_{uuid.uuid4().hex}.log"
        self.random_repo_path = f"/repo_{uuid.uuid4().hex}"
        self.random_source = f"source_{uuid.uuid4().hex}"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_details = f"details_{uuid.uuid4().hex}"
        self.random_telemetry = {"cpu": random.randint(1, 100), "uuid": uuid.uuid4().hex}

    def tearDown(self):
        if os.path.exists(self.random_log_name):
            try:
                os.remove(self.random_log_name)
            except OSError:
                pass
        log_dir = os.path.dirname(self.random_log_name)
        if log_dir and os.path.exists(log_dir):
            try:
                os.rmdir(log_dir)
            except OSError:
                pass

    def test_anomaly_logger_lifecycle(self):
        logger = AnomalyLogger(log_path=self.random_log_name)
        logger.clear_logs()
        
        logger.log_anomaly(
            source=self.random_source,
            severity=self.random_severity,
            details=self.random_details,
            telemetry=self.random_telemetry
        )

        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], self.random_source)
        self.assertEqual(anomalies[0]["severity"], self.random_severity)
        self.assertEqual(anomalies[0]["details"], self.random_details)
        self.assertEqual(anomalies[0]["telemetry"], self.random_telemetry)

        report = logger.get_structured_report()
        self.assertIn("anomalies", report)
        self.assertEqual(len(report["anomalies"]), 1)

        logger.clear_logs()
        self.assertEqual(len(logger.get_anomalies()), 0)

    def test_anomaly_audit_hub(self):
        threshold = random.randint(5, 50)
        hub = AnomalyAuditHub(
            repo_path=self.random_repo_path,
            log_path=self.random_log_name,
            threshold=threshold
        )

        hub.log_anomaly(
            source=self.random_source,
            severity=self.random_severity,
            details=self.random_details,
            telemetry_snapshot=self.random_telemetry
        )

        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.uniform(1.0, 100.0)
        res = hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(res)

        final_report = hub.generate_final_report()
        self.assertIn("report_id", final_report)
        self.assertTrue(final_report["report_id"].endswith(os.path.basename(self.random_log_name)))
        self.assertEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["metrics"][0]["name"], metric_name)
        self.assertEqual(final_report["metrics"][0]["value"], metric_value)
        self.assertEqual(len(final_report["anomalies"]), 1)

    def test_pipeline_starters(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        input_dict = {key: val}

        res_new = start_new(input_dict)
        self.assertTrue(res_new.get("filtered"))
        self.assertEqual(res_new[key], val)

        res_new_raw = start_new(val)
        self.assertTrue(res_new_raw.get("filtered"))
        self.assertEqual(res_new_raw["data"], val)

        res_pipeline = start_pipeline(input_dict)
        self.assertTrue(res_pipeline.get("filtered"))
        self.assertEqual(res_pipeline[key], val)

        res_pipeline_empty = start_pipeline(None)
        self.assertTrue(res_pipeline_empty.get("filtered"))

    def test_extractor_tool(self):
        extractor = ExtractorTool()
        attr_key = f"attr_{uuid.uuid4().hex}"
        attr_val = uuid.uuid4().hex
        tag_str = f'{attr_key}="{attr_val}" other="static"'
        
        parsed = extractor.parse_attributes(tag_str)
        self.assertEqual(parsed.get(attr_key), attr_val)
        self.assertEqual(parsed.get("other"), "static")

        markup_data = f"<div {tag_str}>{uuid.uuid4().hex}</div>"
        extracted = extractor.extract(markup_data)
        self.assertTrue(extracted.get("parsed"))
        self.assertEqual(extracted.get("markup"), markup_data)

    def test_git_inspector(self):
        inspector = GitInspector(repo_path=self.random_repo_path)
        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertIn("commit", history[0])

        commit_hash = uuid.uuid4().hex
        filepath = f"file_{uuid.uuid4().hex}.py"
        content = inspector.read_file_at_commit(commit_hash, filepath)
        self.assertIsInstance(content, bytes)

        analysis = inspector.analyze_repository()
        self.assertIsInstance(analysis, dict)
        self.assertIn("status", analysis)

    def test_anomaly_logger_json_decode_error_resilience(self):
        logger = AnomalyLogger(log_path=self.random_log_name)
        logger.clear_logs()

        with open(self.random_log_name, "w", encoding="utf-8") as f:
            f.write("INVALID_JSON_LINE\n")
            valid_record = {
                "source": self.random_source,
                "severity": self.random_severity,
                "details": self.random_details,
                "telemetry": self.random_telemetry
            }
            f.write(json.dumps(valid_record) + "\n")

        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], self.random_source)

    def telemetry_io_mocking_test(self):
        mock_content = b'random_telemetry_bytes'
        mock_stream = io.BytesIO(mock_content)
        with patch('builtins.open', return_value=mock_stream):
            logger = AnomalyLogger(log_path=self.random_log_name)
            anomalies = logger.get_anomalies()
            self.assertEqual(anomalies, [])