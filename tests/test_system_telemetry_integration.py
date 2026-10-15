import unittest
import tempfile
import time
import uuid
import random
from pathlib import Path

from skills.system_telemetry import SystemTelemetry, TelemetryCollector, TelemetryError

class TestSystemTelemetryIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        self.session_id = str(uuid.uuid4())
        self.telemetry = SystemTelemetry(repo_path=self.repo_path, session_id=self.session_id)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_telemetry_lifecycle_and_aggregation(self):
        cycle_id_1 = f"cycle_{uuid.uuid4()}"
        cycle_id_2 = f"cycle_{uuid.uuid4()}"
        patch_id_1 = f"patch_{uuid.uuid4()}"
        execution_key = f"exec_{uuid.uuid4()}"

        random_lines_delta = random.randint(-50, 100)
        random_error_msg = f"Critical failure {uuid.uuid4()}"

        with self.telemetry.track_cycle(cycle_id_1) as tracker:
            tracker.set_status("SUCCESS")
            time.sleep(0.01)

        try:
            with self.telemetry.track_cycle(cycle_id_2) as tracker:
                time.sleep(0.01)
                raise ValueError("Simulated cycle exception")
        except ValueError:
            pass

        with self.telemetry.track_execution(execution_key):
            time.sleep(0.01)

        self.telemetry.record_patch(
            patch_id=patch_id_1,
            file_path="src/main.py",
            success=True,
            lines_delta=random_lines_delta
        )

        self.telemetry.log_critical_error(
            error=ValueError(random_error_msg),
            context={"module": "patch_verifier", "uuid": str(uuid.uuid4())}
        )

        metrics = self.telemetry.get_metrics()

        cycles = metrics.get("cycles", [])
        self.assertEqual(len(cycles), 2)

        c1 = next(c for c in cycles if c["cycle_id"] == cycle_id_1)
        self.assertEqual(c1["status"], "SUCCESS")
        self.assertGreater(c1["execution_time"], 0.0)

        c2 = next(c for c in cycles if c["cycle_id"] == cycle_id_2)
        self.assertEqual(c2["status"], "FAILED")
        self.assertGreater(c2["execution_time"], 0.0)

        patches = metrics.get("patches", [])
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["patch_id"], patch_id_1)
        self.assertEqual(patches[0]["lines_delta"], random_lines_delta)
        self.assertTrue(patches[0]["success"])

        errors = metrics.get("errors", [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["message"], random_error_msg)
        self.assertIn("uuid", errors[0]["context"])

        exec_metric = metrics.get(execution_key)
        self.assertIsNotNone(exec_metric)
        self.assertTrue(exec_metric["success"])
        self.assertGreater(exec_metric["execution_time"], 0.0)

        export_file = self.repo_path / f"telemetry_{uuid.uuid4()}.json"
        self.telemetry.export_telemetry(export_file)
        self.assertTrue(export_file.exists())
        self.assertGreater(export_file.stat().st_size, 0)

        new_telemetry = SystemTelemetry(repo_path=self.repo_path)
        new_telemetry.load_from_disk(export_file)
        loaded_metrics = new_telemetry.get_metrics()

        self.assertEqual(len(loaded_metrics["cycles"]), 2)
        self.assertEqual(len(loaded_metrics["patches"]), 1)
        self.assertEqual(loaded_metrics["patches"][0]["patch_id"], patch_id_1)

        collector = TelemetryCollector()
        collector.add_session(self.telemetry)
        collector.add_session(new_telemetry)

        summary = collector.aggregate_summary()
        self.assertEqual(summary["total_sessions"], 2)
        self.assertEqual(summary["total_cycles"], 4)
        self.assertGreater(summary["average_execution_time"], 0.0)

    def test_corrupted_telemetry_loading_raises_error(self):
        invalid_file = self.repo_path / f"corrupted_{uuid.uuid4()}.json"
        invalid_file.write_text("{ invalid json payload ...", encoding="utf-8")

        with self.assertRaises(TelemetryError):
            self.telemetry.load_from_disk(invalid_file)

        empty_file = self.repo_path / f"empty_{uuid.uuid4()}.json"
        empty_file.write_text("", encoding="utf-8")

        with self.assertRaises(TelemetryError):
            self.telemetry.load_from_disk(empty_file)

if __name__ == "__main__":
    unittest.main()