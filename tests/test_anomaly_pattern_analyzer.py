import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import os
import json
import io

from skills.anomaly_pattern_analyzer import AnomalyFilter, AnomalyAuditHub, AnomalyLogger, _anomaly_filter_instance, __getattr__


class TestAnomalyPatternAnalyzerInquisition(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.log_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.threshold = random.randint(10, 100)

    def test_anomaly_filter_start_new_valid(self):
        key = f"key_{uuid.uuid4().hex[:6]}"
        val = random.randint(1000, 9999)
        payload = {key: val}

        filter_inst = AnomalyFilter()
        res = filter_inst.start_new(payload)

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "processed")
        self.assertEqual(res.get("filtered_data"), payload)

    def test_anomaly_filter_start_new_invalid(self):
        for invalid_input in [None, {}, [], "string_data", random.randint(1, 100)]:
            filter_inst = AnomalyFilter()
            res = filter_inst.start_new(invalid_input)

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("status"), "error")
            self.assertEqual(res.get("filtered_data"), {})

    def test_module_getattr_anomaly_filter(self):
        inst = __getattr__("anomaly_filter")
        self.assertIs(inst, _anomaly_filter_instance)

        invalid_name = f"attr_{uuid.uuid4().hex}"
        with self.assertRaises(AttributeError):
            __getattr__(invalid_name)

    def test_audit_hub_log_anomaly_and_persistence(self):
        hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)
        src = f"source_{uuid.uuid4().hex[:6]}"
        sev = random.choice(["LOW", "MEDIUM", "CRITICAL"])
        details = f"details_{uuid.uuid4().hex}"
        snap = {f"metric_{uuid.uuid4().hex[:4]}": random.random()}

        mock_file_data = io.StringIO("")
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps([{"details": f"old_{uuid.uuid4().hex}"}]))) as m_file, \
             patch("os.makedirs") as m_dirs:

            hub.log_anomaly(src, sev, details, snap)
            m_dirs.assert_called_once()
            self.assertTrue(m_file.called)

    def test_audit_hub_generate_final_report(self):
        hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)
        report = hub.generate_final_report()
        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("status"), "success")
        self.assertEqual(report.get("report"), "final")

    def test_audit_hub_aggregate_and_report_noop(self):
        hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)
        metric = f"metric_{uuid.uuid4().hex[:6]}"
        val = random.uniform(0.1, 99.9)
        res = hub.aggregate_and_report(metric, val)
        self.assertIsNone(res)

    def test_anomaly_logger_get_anomalies_empty(self):
        logger = AnomalyLogger(self.log_path)
        with patch("os.path.exists", return_value=False):
            res = logger.get_anomalies()
            self.assertEqual(res, [])

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="")):
            res = logger.get_anomalies()
            self.assertEqual(res, [])

    def test_anomaly_logger_get_anomalies_malformed_non_list(self):
        logger = AnomalyLogger(self.log_path)
        random_dict_str = json.dumps({f"key_{uuid.uuid4().hex}": uuid.uuid4().hex})
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_dict_str)):
            res = logger.get_anomalies()
            self.assertEqual(res, [])

    def test_anomaly_logger_get_structured_report(self):
        logger = AnomalyLogger(self.log_path)
        rand_anomaly_msg = f"anomaly_{uuid.uuid4().hex}"
        mock_data = [rand_anomaly_msg, {"source": f"src_{uuid.uuid4().hex}"}]

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
            report = logger.get_structured_report()
            self.assertIsInstance(report, dict)
            self.assertTrue(report.get("structured"))
            anomalies = report.get("anomalies")
            self.assertEqual(len(anomalies), 2)
            self.assertEqual(anomalies[0], {"details": rand_anomaly_msg})


if __name__ == "__main__":
    unittest.main()