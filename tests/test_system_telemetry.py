import os
import json
import unittest
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.system_telemetry import SystemTelemetry, SystemTelemetryError


class TestSystemTelemetry(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"repo_{uuid.uuid4().hex[:8]}"
        self.telemetry = SystemTelemetry(repo_path=self.rand_repo)

    @patch('skills.system_telemetry.psutil')
    def test_collect_performance_metrics_success(self, mock_psutil):
        rand_cpu = random.uniform(1.0, 99.0)
        rand_mem = random.uniform(1.0, 99.0)
        rand_disk = random.uniform(1.0, 99.0)

        mock_psutil.cpu_percent.return_value = rand_cpu
        mock_psutil.virtual_memory.return_value.percent = rand_mem
        mock_psutil.disk_usage.return_value.percent = rand_disk

        metrics = self.telemetry.collect_performance_metrics()

        self.assertEqual(metrics["cpu_percent"], rand_cpu)
        self.assertEqual(metrics["memory_percent"], rand_mem)
        self.assertEqual(metrics["disk_percent"], rand_disk)

    @patch('skills.system_telemetry.psutil')
    def test_collect_performance_metrics_exception(self, mock_psutil):
        rand_err_msg = f"err_{uuid.uuid4().hex}"
        mock_psutil.cpu_percent.side_effect = Exception(rand_err_msg)

        with self.assertRaises(SystemTelemetryError) as ctx:
            self.telemetry.collect_performance_metrics()

        self.assertIn(rand_err_msg, str(ctx.exception))

    @patch('skills.system_telemetry.psutil')
    def test_collect_system_metrics_alias(self, mock_psutil):
        rand_cpu = random.uniform(1.0, 99.0)
        mock_psutil.cpu_percent.return_value = rand_cpu
        mock_psutil.virtual_memory.return_value.percent = 50.0
        mock_psutil.disk_usage.return_value.percent = 50.0

        metrics = self.telemetry.collect_system_metrics()
        self.assertEqual(metrics["cpu_percent"], rand_cpu)

    @patch('skills.system_telemetry.os.path.exists')
    @patch('skills.system_telemetry.open')
    def test_load_telemetry_history_from_file(self, mock_open, mock_exists):
        mock_exists.return_value = True
        rand_patch_id = uuid.uuid4().hex
        rand_status = random.choice(["success", "failed"])
        rand_exec_time = random.randint(1, 100)

        file_content = json.dumps({
            "patch_id": rand_patch_id,
            "status": rand_status,
            "execution_time": rand_exec_time
        }) + "\n"

        mock_file_instance = MagicMock()
        mock_file_instance.__enter__.return_value = [file_content]
        mock_open.return_value = mock_file_instance

        history = self.telemetry._load_telemetry_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["patch_id"], rand_patch_id)
        self.assertEqual(history[0]["status"], rand_status)
        self.assertEqual(history[0]["execution_time"], rand_exec_time)

    @patch('skills.system_telemetry.os.path.exists')
    def test_load_telemetry_history_from_git(self, mock_exists):
        mock_exists.return_value = False
        rand_hexsha = uuid.uuid4().hex

        mock_git_inspector = MagicMock()
        mock_git_inspector.get_commit_history.return_value = [
            {"hexsha": rand_hexsha}
        ]

        telemetry_with_git = SystemTelemetry(
            repo_path=self.rand_repo,
            git_inspector=mock_git_inspector
        )

        history = telemetry_with_git._load_telemetry_history()

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["patch_id"], rand_hexsha)
        self.assertEqual(history[0]["status"], "success")

    @patch('skills.system_telemetry.os.path.exists')
    def test_load_telemetry_history_file_exception(self, mock_exists):
        mock_exists.return_value = True
        rand_err = f"err_load_{uuid.uuid4().hex}"

        with patch('skills.system_telemetry.open', side_effect=Exception(rand_err)):
            with self.assertRaises(SystemTelemetryError) as ctx:
                self.telemetry._load_telemetry_history()
            self.assertIn(rand_err, str(ctx.exception))

    @patch.object(SystemTelemetry, '_load_telemetry_history')
    def test_analyze_patch_success_rate_empty(self, mock_load):
        mock_load.return_value = []
        result = self.telemetry.analyze_patch_success_rate()

        self.assertEqual(result["total_patches"], 0)
        self.assertEqual(result["successful_patches"], 0)
        self.assertEqual(result["failed_patches"], 0)
        self.assertEqual(result["success_rate"], 0.0)

    @patch.object(SystemTelemetry, '_load_telemetry_history')
    def test_analyze_patch_success_rate_calculated(self, mock_load):
        mock_load.return_value = [
            {"status": "success"},
            {"status": "success"},
            {"status": "failed"},
            {"status": "success"}
        ]
        result = self.telemetry.analyze_patch_success_rate()

        self.assertEqual(result["total_patches"], 4)
        self.assertEqual(result["successful_patches"], 3)
        self.assertEqual(result["failed_patches"], 1)
        self.assertAlmostEqual(result["success_rate"], 0.75)

    @patch.object(SystemTelemetry, 'analyze_patch_success_rate')
    def test_analyze_patch_success_alias(self, mock_analyze):
        rand_dict = {"total_patches": random.randint(1, 10)}
        mock_analyze.return_value = rand_dict

        res = self.telemetry.analyze_patch_success()
        self.assertEqual(res, rand_dict)

    @patch.object(SystemTelemetry, 'collect_performance_metrics')
    def test_monitor_resources(self, mock_collect):
        rand_metrics = {"cpu_percent": random.uniform(0, 100)}
        mock_collect.return_value = rand_metrics

        res = self.telemetry.monitor_resources()
        self.assertEqual(res, rand_metrics)

    @patch.object(SystemTelemetry, 'collect_performance_metrics')
    def test_monitor_resources_exception(self, mock_collect):
        rand_err = f"monitor_err_{uuid.uuid4().hex}"
        mock_collect.side_effect = Exception(rand_err)

        with self.assertRaises(SystemTelemetryError) as ctx:
            self.telemetry.monitor_resources()
        self.assertIn(rand_err, str(ctx.exception))

    @patch('skills.system_telemetry.os.makedirs')
    @patch('skills.system_telemetry.open')
    def test_log_telemetry(self, mock_open, mock_makedirs):
        rand_metric_name = f"metric_{uuid.uuid4().hex}"
        rand_metric_val = random.randint(10, 500)

        mock_file_instance = MagicMock()
        mock_file_instance.__enter__.return_value = mock_file_instance
        mock_open.return_value = mock_file_instance

        res = self.telemetry.log_telemetry(rand_metric_name, rand_metric_val)

        self.assertTrue(res)
        mock_makedirs.assert_called_once()
        mock_open.assert_called_once()

        written_arg = mock_file_instance.write.call_args[0][0]
        parsed_payload = json.loads(written_arg)
        self.assertEqual(parsed_payload["metric_name"], rand_metric_name)
        self.assertEqual(parsed_payload["metric_value"], rand_metric_val)
        self.assertIn("timestamp", parsed_payload)

    @patch('skills.system_telemetry.os.makedirs')
    def test_log_telemetry_exception(self, mock_makedirs):
        rand_err = f"log_err_{uuid.uuid4().hex}"
        with patch('skills.system_telemetry.open', side_effect=Exception(rand_err)):
            with self.assertRaises(SystemTelemetryError) as ctx:
                self.telemetry.log_telemetry("some_metric", 123)
            self.assertIn(rand_err, str(ctx.exception))

    @patch('skills.system_telemetry.os.path.exists')
    @patch('skills.system_telemetry.open')
    def test_read_telemetry_stream_exists(self, mock_open, mock_exists):
        mock_exists.return_value = True
        rand_line_1 = f"line_{uuid.uuid4().hex}"
        rand_line_2 = f"line_{uuid.uuid4().hex}"

        mock_file_instance = MagicMock()
        mock_file_instance.__enter__.return_value = [f"{rand_line_1}\n", f"  {rand_line_2}  \n"]
        mock_open.return_value = mock_file_instance

        rand_stream_id = uuid.uuid4().hex
        lines = self.telemetry.read_telemetry_stream(rand_stream_id)

        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], rand_line_1)
        self.assertEqual(lines[1], rand_line_2)

    @patch('skills.system_telemetry.os.path.exists')
    def test_read_telemetry_stream_not_exists(self, mock_exists):
        mock_exists.return_value = False
        rand_stream_id = uuid.uuid4().hex

        lines = self.telemetry.read_telemetry_stream(rand_stream_id)

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], f"{rand_stream_id}:42")

    @patch('skills.system_telemetry.os.path.exists')
    def test_read_telemetry_stream_exception(self, mock_exists):
        mock_exists.return_value = True
        rand_err = f"read_err_{uuid.uuid4().hex}"

        with patch('skills.system_telemetry.open', side_effect=Exception(rand_err)):
            with self.assertRaises(SystemTelemetryError) as ctx:
                self.telemetry.read_telemetry_stream(uuid.uuid4().hex)
            self.assertIn(rand_err, str(ctx.exception))