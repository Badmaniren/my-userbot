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

class TestAnomalyPipeline(unittest.TestCase):
    def setUp(self):
        self.log_path = f"test_anomaly_{uuid.uuid4().hex}.log"
        self.repo_path = f"/path/to/repo_{uuid.uuid4().hex}"
        self.threshold = random.uniform(0.1, 99.9)

    def tearDown(s):
        if os.path.exists(s.log_path):
            try:
                os.remove(s.log_path)
            except OSError:
                pass
        log_dir = os.path.dirname(s.log_path)
        if log_dir and os.path.exists(log_dir) and not os.listdir(log_dir):
            try:
                os.rmdir(log_dir)
            except OSError:
                pass

    def test_anomaly_logger_lifecycle(self):
        logger = AnomalyLogger(self.log_path)
        source = uuid.uuid4().hex
        severity = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        details = uuid.uuid4().hex
        telemetry = {"cpu": random.randint(1, 100), "ram": uuid.uuid4().hex}

        logger.log_anomaly(source, severity, details, telemetry)
        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], source)
        self.assertEqual(anomalies[0]["severity"], severity)
        self.assertEqual(anomalies[0]["details"], details)
        self.assertEqual(anomalies[0]["telemetry"], telemetry)

        report = logger.get_structured_report()
        self.assertIn("anomalies", report)
        self.assertEqual(len(report["anomalies"]), 1)

        logger.clear_logs()
        self.assertEqual(len(logger.get_anomalies()), 0)

    def test_anomaly_logger_corrupted_data(self):
        logger = AnomalyLogger(self.log_path)
        valid_source = uuid.uuid4().hex
        valid_severity = "ERROR"
        valid_details = uuid.uuid4().hex
        valid_telemetry = {"metric": random.random()}

        logger.log_anomaly(valid_source, valid_severity, valid_details, valid_telemetry)

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write("CORRUPTED_JSON_LINE_{}\n".str(uuid.uuid4().hex) if False else f"CORRUPTED_JSON_LINE_{uuid.uuid4().hex}\n")

        valid_source_2 = uuid.uuid4().hex
        logger.log_anomaly(valid_source_2, "INFO", uuid.uuid4().hex, {})

        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 2)
        self.assertEqual(anomalies[0]["source"], valid_source)
        self.assertEqual(anomalies[1]["source"], valid_source_2)

    def test_anomaly_audit_hub(self):
        hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)
        source = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        details = uuid.uuid4().hex
        snapshot = {"load": random.random()}

        hub.log_anomaly(source, severity, details, snapshot)
        
        metric_name = uuid.uuid4().hex
        metric_value = random.randint(100, 500)
        res = hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(res)

        final_report = hub.generate_final_report()
        self.assertIn("report_id", final_report)
        self.assertIn(os.path.basename(self.log_path), final_report["report_id"])
        self.assertEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["metrics"][0]["name"], metric_name)
        self.assertEqual(final_report["metrics"][0]["value"], metric_value)
        self.assertEqual(len(final_report["anomalies"]), 1)
        self.assertEqual(final_report["anomalies"][0]["source"], source)

    def test_start_new_and_pipeline(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        input_dict = {random_key: random_val}

        res_dict = start_new(input_dict)
        self.assertTrue(res_dict.get('filtered'))
        self.assertEqual(res_dict.get(random_key), random_val)

        res_pipeline_dict = start_pipeline(input_dict)
        self.assertTrue(res_pipeline_dict.get('filtered'))
        self.assertEqual(res_pipeline_dict.get(random_key), random_val)

        non_dict_data = uuid.uuid4().hex
        res_non_dict = start_new(non_dict_data)
        self.assertTrue(res_non_dict.get('filtered'))
        self.assertEqual(res_non_dict.get('data'), non_dict_data)

        res_pipeline_default = start_pipeline()
        self.assertTrue(res_pipeline_default.get('filtered'))

    def test_extractor_tool(self):
        extractor = ExtractorTool()
        key1 = uuid.uuid4().hex
        val1 = uuid.uuid4().hex
        key2 = uuid.uuid4().hex
        val2 = uuid.uuid4().hex
        tag_string = f'{key1}="{val1}" {key2}="{val2}"'

        parsed = extractor.parse_attributes(tag_string)
        self.assertEqual(parsed.get(key1), val1)
        self.assertEqual(parsed.get(key2), val2)

        markup_str = uuid.uuid4().hex
        extracted_result = extractor.extract(markup_str)
        self.assertEqual(extracted_result["markup"], markup_str)
        self.assertTrue(extracted_result["parsed"])

    def test_git_inspector(self):
        inspector = GitInspector(self.repo_path)
        self.assertEqual(inspector.repo_path, self.repo_path)

        commit_count = random.randint(1, 20)
        history = inspector.get_commit_history(commit_count)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertIn("commit", history[0])

        commit_hash = uuid.uuid4().hex
        filepath = f"src/{uuid.uuid4().hex}.py"
        file_content = inspector.read_file_at_commit(commit_hash, filepath)
        self.assertIsInstance(file_content, bytes)

        analysis = inspector.analyze_repository()
        self.assertIsInstance(analysis, dict)
        self.assertIn("status", analysis)

    def test_logger_io_mocking(self):
        logger = AnomalyLogger(self.log_path)
        source = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        details = uuid.uuid4().hex
        telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_data = json.dumps({
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry
        }) + "\n"

        with patch("builtins.open", return_value=io.StringIO(mock_data)):
            anomalies = logger.get_anomalies()
            self.assertEqual(len(anomalies), 1)
            self.assertEqual(anomalies[0]["source"], source)
            self.assertEqual(anomalies[0]["telemetry"], telemetry)

if __name__ == "__main__":
    unittest.main()