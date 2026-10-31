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
        self.random_filename = f"{uuid.uuid4().hex}.log"
        self.random_repo = f"/path/to/{uuid.uuid4().hex}"
        self.random_threshold = random.uniform(0.1, 99.9)

    def tearDown(self):
        if os.path.exists(self.random_filename):
            try:
                os.remove(self.random_filename)
            except OSError:
                pass
            
        log_dir = os.path.dirname(self.random_filename)
        if log_dir and os.path.exists(log_dir) and not os.listdir(log_dir):
            try:
                os.rmdir(log_dir)
            except OSError:
                pass

    def test_anomaly_logger_lifecycle(self):
        logger = AnomalyLogger(self.random_filename)
        
        source = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = uuid.uuid4().hex
        telemetry = {"cpu": random.randint(1, 100), "mem": random.randint(1, 100)}
        
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
        self.assertEqual(logger.get_anomalies(), [])

    def test_anomaly_logger_corrupted_json(self):
        logger = AnomalyLogger(self.random_filename)
        garbage = uuid.uuid4().hex
        
        with open(self.random_filename, "w", encoding="utf-8") as f:
            f.write(garbage + "\n")
            
        anomalies = logger.get_anomalies()
        self.assertEqual(anomalies, [])

    def test_anomaly_audit_hub(self):
        hub = AnomalyAuditHub(self.random_repo, self.random_filename, self.random_threshold)
        
        source = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        details = uuid.uuid4().hex
        snapshot = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        hub.log_anomaly(source, severity, details, snapshot)
        
        metric_name = uuid.uuid4().hex
        metric_value = random.randint(100, 999)
        res = hub.aggregate_and_report(metric_name, metric_value)
        self.assertTrue(res)
        
        final_report = hub.generate_final_report()
        self.assertIn("report_id", final_report)
        self.assertTrue(final_report["report_id"].endswith(os.path.basename(self.random_filename)))
        self.assertEqual(len(final_report["metrics"]), 1)
        self.assertEqual(final_report["metrics"][0]["name"], metric_name)
        self.assertEqual(final_report["metrics"][0]["value"], metric_value)
        self.assertEqual(len(final_report["anomalies"]), 1)
        self.assertEqual(final_report["anomalies"][0]["source"], source)

    def test_start_new_with_dict(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        input_dict = {key: val}
        
        result = start_new(input_dict)
        self.assertTrue(result['filtered'])
        self.assertEqual(result[key], val)

    def test_start_new_with_non_dict(self):
        input_val = uuid.uuid4().hex
        result = start_new(input_val)
        self.assertTrue(result['filtered'])
        self.assertEqual(result['data'], input_val)

    def test_start_pipeline(self):
        res_empty = start_pipeline()
        self.assertTrue(res_empty['filtered'])
        
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        res_custom = start_pipeline({key: val})
        self.assertTrue(res_custom['filtered'])
        self.assertEqual(res_custom[key], val)

    def test_extractor_tool(self):
        extractor = ExtractorTool()
        markup_val = uuid.uuid4().hex
        extract_res = extractor.extract(markup_val)
        self.assertEqual(extract_res["markup"], markup_val)
        self.assertTrue(extract_res["parsed"])
        
        attr_key = uuid.uuid4().hex[:8]
        attr_val = uuid.uuid4().hex[:8]
        tag_string = f'<div {attr_key}="{attr_val}"></div>'
        parsed_attrs = extractor.parse_attributes(tag_string)
        self.assertIn(attr_key, parsed_attrs)
        self.assertEqual(parsed_attrs[attr_key], attr_val)

    def test_git_inspector(self):
        inspector = GitInspector(self.random_repo)
        history = inspector.get_commit_history()
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertIn("commit", history[0])
        
        commit_hash = uuid.uuid4().hex
        filepath = f"{uuid.uuid4().hex}.py"
        content = inspector.read_file_at_commit(commit_hash, filepath)
        self.assertIsInstance(content, bytes)
        
        analysis = inspector.analyze_repository()
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get("status"), "clean")

if __name__ == '__main__':
    unittest.main()