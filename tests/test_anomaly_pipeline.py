import unittest
from unittest.mock import patch, mock_open
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

class TestAnomalyPipelineInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_log_name = f"log_{uuid.uuid4().hex}.log"
        self.rand_repo_path = f"/repo_{uuid.uuid4().hex}"
        self.rand_source = f"src_{uuid.uuid4().hex}"
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.rand_details = f"details_{uuid.uuid4().hex}"
        self.rand_telemetry = {"cpu": random.randint(1, 100), "memory": uuid.uuid4().hex}

    def tearDown(self):
        if os.path.exists(self.rand_log_name):
            try:
                os.remove(self.rand_log_name)
            except OSError:
                pass

    def test_anomaly_logger_lifecycle(self):
        logger = AnomalyLogger(log_path=self.rand_log_name)
        logger.clear_logs()
        
        logger.log_anomaly(
            self.rand_source,
            self.rand_severity,
            self.rand_details,
            self.rand_telemetry
        )
        
        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], self.rand_source)
        self.assertEqual(anomalies[0]["severity"], self.rand_severity)
        self.assertEqual(anomalies[0]["details"], self.rand_details)
        self.assertEqual(anomalies[0]["telemetry"], self.rand_telemetry)

        report = logger.get_structured_report()
        self.assertIn("anomalies", report)
        self.assertEqual(len(report["anomalies"]), 1)

        logger.clear_logs()
        self.assertEqual(len(logger.get_anomalies()), 0)

    def test_anomaly_logger_json_decode_error_resilience(self):
        corrupted_data = f"{uuid.uuid4().hex}\n" + json.dumps({
            "source": self.rand_source,
            "severity": self.rand_severity,
            "details": self.rand_details,
            "telemetry": self.rand_telemetry
        }) + "\n"

        with patch("builtins.open", mock_open(read_data=corrupted_data)):
            with patch("os.path.exists", return_value=True):
                logger = AnomalyLogger(log_path=self.rand_log_name)
                anomalies = logger.get_anomalies()
                self.assertEqual(len(anomalies), 1)
                self.assertEqual(anomalies[0]["source"], self.rand_source)

    def test_anomaly_audit_hub_operations(self):
        threshold = random.randint(10, 100)
        hub = AnomalyAuditHub(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_name,
            threshold=threshold
        )
        
        hub.log_anomaly(
            self.rand_source,
            self.rand_severity,
            self.rand_details,
            self.rand_telemetry
        )

        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.randint(1, 1000)
        agg_res = hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(agg_res)

        final_report = hub.generate_final_report()
        self.assertIn("report_id", final_report)
        self.assertIn(os.path.basename(self.rand_log_name), final_report["report_id"])
        self.assertEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["metrics"][0]["name"], metric_name)
        self.assertEqual(final_report["metrics"][0]["value"], metric_value)
        self.assertEqual(len(final_report["anomalies"]), 1)

    def test_anomaly_filter_start_new(self):
        input_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        res_dict = start_new(input_data)
        self.assertTrue(res_dict.get("filtered"))
        for k, v in input_data.items():
            self.assertEqual(res_dict[k], v)

        non_dict_data = uuid.uuid4().hex
        res_non_dict = start_new(non_dict_data)
        self.assertTrue(res_non_dict.get("filtered"))
        self.assertEqual(res_non_dict["data"], non_dict_data)

    def test_start_pipeline_wrapper(self):
        res_empty = start_pipeline()
        self.assertTrue(res_empty.get("filtered"))

        custom_input = {uuid.uuid4().hex: uuid.uuid4().hex}
        res_custom = start_pipeline(custom_input)
        self.assertTrue(res_custom.get("filtered"))
        self.assertEqual(res_custom.get(list(custom_input.keys())[0]), list(custom_input.values())[0])

    def test_extractor_tool_parsing(self):
        key1, val1 = uuid.uuid4().hex, uuid.uuid4().hex
        key2, val2 = uuid.uuid4().hex, uuid.uuid4().hex
        tag_string = f'id="{key1}"="{val1}" class="{key2}"="{val2}" data-test="{uuid.uuid4().hex}"'
        
        extractor = ExtractorTool()
        parsed = extractor.parse_attributes(tag_string)
        self.assertIsInstance(parsed, dict)

        rand_markup = f"<div><{uuid.uuid4().hex}></div>"
        extracted = extractor.extract(rand_markup)
        self.assertEqual(extracted["markup"], rand_markup)
        self.assertTrue(extracted["parsed"])

    def test_git_inspector_mock_behavior(self):
        inspector = GitInspector(repo_path=self.rand_repo_path)
        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertIn("commit", history[0])

        commit_hash = uuid.uuid4().hex
        filepath = f"src/{uuid.uuid4().hex}.py"
        file_content = inspector.read_file_at_commit(commit_hash, filepath)
        self.assertIsInstance(file_content, bytes)

        repo_analysis = inspector.analyze_repository()
        self.assertIn("status", repo_analysis)

    def test_full_anomaly_pipeline_integration_flow(self):
        logger = AnomalyLogger(log_path=self.rand_log_name)
        logger.clear_logs()

        hub = AnomalyAuditHub(
            repo_path=self.rand_repo_path,
            log_path=self.rand_log_name,
            threshold=random.randint(5, 50)
        )

        hub.log_anomaly(
            self.rand_source,
            self.rand_severity,
            self.rand_details,
            self.rand_telemetry
        )

        metric_name = uuid.uuid4().hex
        metric_value = random.random() * 100
        hub.aggregate_and_report(metric_name, metric_value)

        report = hub.generate_final_report()
        self.assertEqual(len(report["anomalies"]), 1)
        self.assertEqual(report["anomalies"][0]["details"], self.rand_details)
        self.assertEqual(report["metrics"][0]["value"], metric_value)

    def test_io_stream_safety_with_bytes(self):
        stream_data = uuid.uuid4().bytes
        stream = io.BytesIO(stream_data)
        content = stream.read()
        self.assertEqual(content, stream_data)