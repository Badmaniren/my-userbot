import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.patch_auto_executor import auto_patch_pipeline, patch_scheduler, error_recovery_hub, PipelineResult


class TestPatchAutoExecutorInquisitor(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.incident_id = uuid.uuid4().hex
        self.error_msg = "".join(random.choices(string.ascii_letters + string.whitespace, k=32))
        self.traceback_str = f"Traceback (most recent call last):\n  File '{uuid.uuid4().hex}.py', line {random.randint(1, 100)}\n    raise Exception('{self.error_msg}')"
        self.exception_obj = RuntimeError(self.error_msg)
        self.patch_payload = {
            "patch_id": uuid.uuid4().hex,
            "diff": f"--- a/{uuid.uuid4().hex}.py\n+++ b/{uuid.uuid4().hex}.py\n@@ -1,1 +1,1 @@\n-{self.error_msg}\n+{uuid.uuid4().hex}"
        }

    @patch('skills.patch_auto_executor.PatchScheduler')
    @patch('skills.patch_auto_executor.ErrorRecoveryHub')
    def test_composition_and_execution_success(self, mock_hub_class, mock_scheduler_class):
        mock_hub = mock_hub_class.return_value
        mock_scheduler = mock_scheduler_class.return_value

        mock_hub.capture_failure.return_value = self.incident_id
        mock_hub.analyze_failure.return_value = {"status": "analyzed", "id": self.incident_id}
        mock_hub.generate_patch.return_value = self.patch_payload
        mock_hub.deploy_and_verify.return_value = True

        mock_scheduler.coordinate_and_schedule.return_value = True

        result = auto_patch_pipeline(self.module_name, self.exception_obj, self.traceback_str)

        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertEqual(result.incident_id, self.incident_id)
        self.assertEqual(result.patch_data, self.patch_payload)

        mock_hub.capture_failure.assert_called_once_with(self.module_name, self.exception_obj, self.traceback_str)
        mock_scheduler.coordinate_and_schedule.assert_called_once()

    @patch('skills.patch_auto_executor.PatchScheduler')
    @patch('skills.patch_auto_executor.ErrorRecoveryHub')
    def test_pipeline_failure_recovery_flow(self, mock_hub_class, mock_scheduler_class):
        mock_hub = mock_hub_class.return_value
        mock_scheduler = mock_scheduler_class.return_value

        mock_hub.capture_failure.return_value = self.incident_id
        mock_hub.analyze_failure.return_value = {"status": "critical"}
        mock_hub.generate_patch.return_value = self.patch_payload
        mock_hub.deploy_and_verify.return_value = False

        mock_scheduler.coordinate_and_schedule.return_value = False

        result = auto_patch_pipeline(self.module_name, self.exception_obj, self.traceback_str)

        self.assertIsInstance(result, PipelineResult)
        self.assertFalse(result.success)
        self.assertEqual(result.incident_id, self.incident_id)
        self.assertIn(self.error_msg, str(result.error))

    def test_stream_processing_with_io_mock(self):
        random_stream_data = f"STREAM_DATA_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.patch_auto_executor.PatchScheduler') as mock_scheduler_class:
            mock_scheduler = mock_scheduler_class.return_value
            mock_scheduler.process_stream.return_value = {
                "processed": True,
                "stream_hash": uuid.uuid4().hex
            }

            from skills.patch_auto_executor import execute_stream_patch_pipeline
            res = execute_stream_patch_pipeline(self.module_name, mock_stream)

            self.assertTrue(res["processed"])
            mock_scheduler.process_stream.assert_called_once_with(self.module_name, mock_stream)

    @patch('skills.patch_auto_executor.ErrorRecoveryHub')
    def test_batch_failures_handling(self, mock_hub_class):
        mock_hub = mock_hub_class.return_value
        failures_count = random.randint(2, 5)
        failures_list = []
        for _ in range(failures_count):
            failures_list.append({
                "module": f"mod_{uuid.uuid4().hex[:4]}",
                "exc": ValueError(uuid.uuid4().hex),
                "tb": uuid.uuid4().hex
            })

        mock_hub.analyze_and_recover.return_value = [uuid.uuid4().hex for _ in range(failures_count)]

        with patch('skills.patch_auto_executor.PatchScheduler') as mock_scheduler_class:
            mock_scheduler = mock_scheduler_class.return_value
            mock_scheduler.batch_schedule.return_value = True

            from skills.patch_auto_executor import batch_auto_patch_runner
            batch_res = batch_auto_patch_runner(failures_list)

            self.assertTrue(batch_res)
            mock_scheduler.batch_schedule.assert_called_once_with(failures_list)


if __name__ == '__main__':
    unittest.main()