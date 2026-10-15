import unittest
import json
import time
import io
import random
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

from skills.system_telemetry import (
    TelemetryError,
    CycleTracker,
    ExecutionTracker,
    SystemTelemetry,
    TelemetryCollector
)

class TestSystemTelemetryInquisitor(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.session_id = uuid.uuid4().hex
        self.telemetry = SystemTelemetry(repo_path=self.repo_path, session_id=self.session_id)

    def test_initial_state(self):
        metrics = self.telemetry.get_metrics()
        self.assertEqual(metrics["cycles"], [])
        self.assertEqual(metrics["patches"], [])
        self.assertEqual(metrics["errors"], [])
        self.assertEqual(self.telemetry.repo_path, self.repo_path)
        self.assertEqual(self.telemetry.session_id, self.session_id)

    def test_cycle_tracker_success(self):
        cycle_id = uuid.uuid4().hex
        with self.telemetry.track_cycle(cycle_id) as tracker:
            tracker.set_status("SUCCESS")
            time.sleep(0.01)

        metrics = self.telemetry.get_metrics()
        self.assertEqual(len(metrics["cycles"]), 1)
        record = metrics["cycles"][0]
        self.assertEqual(record["cycle_id"], cycle_id)
        self.assertEqual(record["status"], "SUCCESS")
        self.assertGreater(record["execution_time"], 0.0)

    def test_cycle_tracker_failure_on_exception(self):
        cycle_id = uuid.uuid4().hex
        err_msg = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            with self.telemetry.track_cycle(cycle_id) as tracker:
                raise ValueError(err_msg)

        metrics = self.telemetry.get_metrics()
        self.assertEqual(len(metrics["cycles"]), 1)
        record = metrics["cycles"][0]
        self.assertEqual(record["cycle_id"], cycle_id)
        self.assertEqual(record["status"], "FAILED")

    def test_execution_tracker_metrics(self):
        key = uuid.uuid4().hex
        with self.telemetry.track_execution(key):
            time.sleep(0.01)

        self.assertIn(key, self.telemetry.metrics)
        self.assertTrue(self.telemetry.metrics[key]["success"])
        self.assertGreater(self.telemetry.metrics[key]["execution_time"], 0.0)

    def test_execution_tracker_failure(self):
        key = uuid.uuid4().hex
        err_msg = uuid.uuid4().hex
        with self.assertRaises(KeyError):
            with self.telemetry.track_execution(key):
                raise KeyError(err_msg)

        self.assertIn(key, self.telemetry.metrics)
        self.assertFalse(self.telemetry.metrics[key]["success"])

    def test_record_patch(self):
        patch_id = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        success = random.choice([True, False])
        lines_delta = random.randint(-100, 100)

        self.telemetry.record_patch(patch_id, file_path, success, lines_delta)
        patches = self.telemetry.get_metrics()["patches"]
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["patch_id"], patch_id)
        self.assertEqual(patches[0]["file_path"], file_path)
        self.assertEqual(patches[0]["success"], success)
        self.assertEqual(patches[0]["lines_delta"], lines_delta)

    def test_log_critical_error(self):
        err_msg = uuid.uuid4().hex
        context_key = uuid.uuid4().hex
        context_val = uuid.uuid4().hex
        context = {context_key: context_val}

        self.telemetry.log_critical_error(Exception(err_msg), context=context)
        errors = self.telemetry.get_metrics()["errors"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["message"], err_msg)
        self.assertEqual(errors[0]["context"], context)
        self.assertIsInstance(errors[0]["timestamp"], float)

    def test_telemetry_export_to_io_stream(self):
        cycle_id = uuid.uuid4().hex
        self.telemetry.record_cycle_manual(cycle_id, 0.42, "SUCCESS")

        export_path = io.BytesIO()
        self.telemetry.export_telemetry(export_path)
        export_path.seek(0)
        content = export_path.read()
        self.assertIsInstance(content, bytes)

        data = json.loads(content.decode("utf-8"))
        self.assertEqual(data["cycles"][0]["cycle_id"], cycle_id)

    def test_telemetry_export_to_text_stream(self):
        cycle_id = uuid.uuid4().hex
        self.telemetry.record_cycle_manual(cycle_id, 0.55, "FAILED")

        export_path = io.StringIO()
        self.telemetry.export_telemetry(export_path)
        export_path.seek(0)
        content = export_path.read()
        self.assertIsInstance(content, str)

        data = json.loads(content)
        self.assertEqual(data["cycles"][0]["cycle_id"], cycle_id)

    def test_telemetry_export_to_file(self):
        cycle_id = uuid.uuid4().hex
        self.telemetry.record_cycle_manual(cycle_id, 1.23, "SUCCESS")

        file_name = f"{uuid.uuid4().hex}.json"
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            self.telemetry.export_telemetry(file_name)
            mock_file.assert_called_once_with(file_name, "w", encoding="utf-8")

    def test_load_from_disk_stream(self):
        cycle_id = uuid.uuid4().hex
        payload = json.dumps({
            "cycles": [{"cycle_id": cycle_id, "execution_time": 0.1, "status": "SUCCESS"}],
            "patches": [],
            "errors": []
        }).encode("utf-8")

        stream = io.BytesIO(payload)
        new_telemetry = SystemTelemetry()
        new_telemetry.load_from_disk(stream)

        metrics = new_telemetry.get_metrics()
        self.assertEqual(metrics["cycles"][0]["cycle_id"], cycle_id)

    def test_load_from_disk_invalid_json(self):
        stream = io.BytesIO(b"{invalid_json")
        new_telemetry = SystemTelemetry()
        with self.assertRaises(TelemetryError):
            new_telemetry.load_from_disk(stream)

    def test_load_from_disk_empty_stream(self):
        stream = io.BytesIO(b"   ")
        new_telemetry = SystemTelemetry()
        with self.assertRaises(TelemetryError):
            new_telemetry.load_from_disk(stream)

    def test_load_from_disk_unicode_error(self):
        bad_bytes = b"\xff\xfe\xfd"
        stream = io.BytesIO(bad_bytes)
        new_telemetry = SystemTelemetry()
        with self.assertRaises(TelemetryError):
            new_telemetry.load_from_disk(stream)

    def test_load_from_disk_file_not_found(self):
        file_path = f"{uuid.uuid4().hex}.json"
        new_telemetry = SystemTelemetry()
        with patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(TelemetryError):
                new_telemetry.load_from_disk(file_path)

    def test_telemetry_collector_aggregation(self):
        collector = TelemetryCollector()

        t1 = SystemTelemetry()
        c1_id = uuid.uuid4().hex
        t1.record_cycle_manual(c1_id, 2.0, "SUCCESS")

        t2 = SystemTelemetry()
        c2_id = uuid.uuid4().hex
        c3_id = uuid.uuid4().hex
        t2.record_cycle_manual(c2_id, 1.0, "SUCCESS")
        t2.record_cycle_manual(c3_id, 3.0, "FAILED")

        collector.add_session(t1)
        collector.add_session(t2)

        summary = collector.aggregate_summary()
        self.assertEqual(summary["total_sessions"], 2)
        self.assertEqual(summary["total_cycles"], 3)
        self.assertEqual(summary["average_execution_time"], 2.0)

    def test_telemetry_collector_empty(self):
        collector = TelemetryCollector()
        summary = collector.aggregate_summary()
        self.assertEqual(summary["total_sessions"], 0)
        self.assertEqual(summary["total_cycles"], 0)
        self.assertEqual(summary["average_execution_time"], 0.0)