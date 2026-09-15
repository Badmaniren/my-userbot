import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from skills.patch_scheduler import PatchScheduler
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.auto_patch_pipeline import PipelineResult


class TestPatchScheduler(unittest.TestCase):

    def setUp(self):
        self.scheduler = PatchScheduler()

    def test_schedule_and_apply_patch_success(self):
        rand_module = f"mod_{uuid.uuid4().hex[:8]}"
        rand_exc_msg = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        rand_exc = RuntimeError(rand_exc_msg)
        rand_tb = f"Traceback at {uuid.uuid4().hex}"
        rand_incident_id = uuid.uuid4().hex

        mock_hub = MagicMock(spec=ErrorRecoveryHub)
        mock_hub.capture_failure.return_value = rand_incident_id
        mock_hub.analyze_and_recover.return_value = PipelineResult(
            success=True,
            incident_id=rand_incident_id,
            error=None,
            raw_result=None,
            patch_data={"code": "print('fixed')"}
        )

        with patch('skills.patch_scheduler.ErrorRecoveryHub', return_value=mock_hub):
            result = self.scheduler.schedule_patch(rand_module, rand_exc, rand_tb)
            
            self.assertTrue(result.success)
            self.assertEqual(result.incident_id, rand_incident_id)
            mock_hub.capture_failure.assert_called_once_with(rand_module, rand_exc, rand_tb)
            mock_hub.analyze_and_recover.assert_called_once()

    def test_schedule_patch_failure_flow(self):
        rand_module = f"service_{uuid.uuid4().hex[:6]}"
        rand_exc = ValueError(uuid.uuid4().hex)
        rand_tb = f"File '<string>', line {random.randint(1, 100)}"
        rand_incident_id = uuid.uuid4().hex
        rand_error_reason = uuid.uuid4().hex

        mock_hub = MagicMock(spec=ErrorRecoveryHub)
        mock_hub.capture_failure.return_value = rand_incident_id
        mock_hub.analyze_and_recover.return_value = PipelineResult(
            success=False,
            incident_id=rand_incident_id,
            error=rand_error_reason,
            raw_result=None,
            patch_data=None
        )

        with patch('skills.patch_scheduler.ErrorRecoveryHub', return_value=mock_hub):
            result = self.scheduler.schedule_patch(rand_module, rand_exc, rand_tb)
            
            self.assertFalse(result.success)
            self.assertEqual(result.incident_id, rand_incident_id)
            self.assertEqual(result.error, rand_error_reason)

    def test_batch_schedule_patches(self):
        modules_count = random.randint(2, 5)
        failures = []
        for _ in range(modules_count):
            failures.append({
                "module_name": f"mod_{uuid.uuid4().hex[:4]}",
                "exception": TypeError(uuid.uuid4().hex),
                "traceback": uuid.uuid4().hex
            })

        mock_hub = MagicMock(spec=ErrorRecoveryHub)
        mock_hub.analyze_and_recover.side_effect = [
            PipelineResult(
                success=True,
                incident_id=uuid.uuid4().hex,
                error=None,
                raw_result=None,
                patch_data={}
            ) for _ in range(modules_count)
        ]

        with patch('skills.patch_scheduler.ErrorRecoveryHub', return_value=mock_hub):
            results = self.scheduler.batch_schedule(failures)
            
            self.assertEqual(len(results), modules_count)
            for res in results:
                self.assertTrue(res.success)

    def test_scheduler_stream_processing_with_io(self):
        rand_stream_data = f"incident_stream_{uuid.uuid4().hex}".encode('utf-8')
        stream_mock = io.BytesIO(rand_stream_data)

        rand_module = f"stream_mod_{uuid.uuid4().hex[:5]}"
        mock_hub = MagicMock(spec=ErrorRecoveryHub)
        mock_hub.analyze_and_recover.return_value = PipelineResult(
            success=True,
            incident_id=uuid.uuid4().hex,
            error=None,
            raw_result=stream_mock.read().decode('utf-8'),
            patch_data=None
        )

        with patch('skills.patch_scheduler.ErrorRecoveryHub', return_value=mock_hub):
            result = self.scheduler.process_stream(rand_module, stream_mock)
            self.assertTrue(result.success)
            self.assertIn("incident_stream", result.raw_result)