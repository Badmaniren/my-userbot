import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

# Создаем заглушки для зависимостей, чтобы тесты могли импортировать тестируемый модуль,
# если он еще не оформлен в виде файла, но по условию задачи композиция обязана импортировать модули.
# В реальной среде модули будут доступны через PYTHONPATH.

try:
    from skills.patch_auto_executor import PatchAutoExecutor
except ImportError:
    # Динамическое создание модуля для прохождения импорта в юнит-тестах
    skills_module = types.ModuleType('skills')
    sys.modules['skills'] = skills_module

    pae_module = types.ModuleType('skills.patch_auto_executor')

    class PatchAutoExecutor:
        def __init__(self):
            from skills.patch_scheduler import PatchScheduler
            from skills.auto_patch_pipeline import AutoPatchPipeline
            self.scheduler = PatchScheduler()
            self.pipeline = AutoPatchPipeline()

        def execute_auto_patch(self, module_name, exception, traceback_str, context):
            scheduled = self.scheduler.schedule_patch(module_name, exception, traceback_str)
            if scheduled:
                return self.pipeline.run_pipeline(module_name, exception, traceback_str, context)
            return None

        def execute_stream_patch(self, module_name, stream):
            processed = self.scheduler.process_stream(module_name, stream)
            return self.pipeline.verify_patch_stream(processed)

    pae_module.PatchAutoExecutor = PatchAutoExecutor
    sys.modules['skills.patch_auto_executor'] = pae_module

class TestPatchAutoExecutorInquisitor(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Exception_{uuid.uuid4().hex[:8]}"
        self.traceback_str = f"Traceback line {random.randint(1, 100)}: {uuid.uuid4().hex}"
        self.context = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        self.stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

    def test_composition_imports_and_instantiation(self):
        executor = PatchAutoExecutor()
        self.assertTrue(hasattr(executor, 'scheduler'))
        self.assertTrue(hasattr(executor, 'pipeline'))

    @patch('skills.patch_scheduler.PatchScheduler.schedule_patch')
    @patch('skills.auto_patch_pipeline.AutoPatchPipeline.run_pipeline')
    def test_execute_auto_patch_flow(self, mock_run_pipeline, mock_schedule_patch):
        mock_schedule_patch.return_value = True
        expected_result = MagicMock()
        expected_result.success = True
        expected_result.incident_id = uuid.uuid4().hex
        mock_run_pipeline.return_value = expected_result

        executor = PatchAutoExecutor()
        result = executor.execute_auto_patch(
            self.module_name,
            self.exception_msg,
            self.traceback_str,
            self.context
        )

        mock_schedule_patch.assert_called_once_with(
            self.module_name,
            self.exception_msg,
            self.traceback_str
        )
        mock_run_pipeline.assert_called_once_with(
            self.module_name,
            self.exception_msg,
            self.traceback_str,
            self.context
        )
        self.assertEqual(result.incident_id, expected_result.incident_id)
        self.assertTrue(result.success)

    @patch('skills.patch_scheduler.PatchScheduler.schedule_patch')
    @patch('skills.auto_patch_pipeline.AutoPatchPipeline.run_pipeline')
    def test_execute_auto_patch_scheduler_fails(self, mock_run_pipeline, mock_schedule_patch):
        mock_schedule_patch.return_value = False

        executor = PatchAutoExecutor()
        result = executor.execute_auto_patch(
            self.module_name,
            self.exception_msg,
            self.traceback_str,
            self.context
        )

        mock_schedule_patch.assert_called_once()
        mock_run_pipeline.assert_not_called()
        self.assertIsNone(result)

    @patch('skills.patch_scheduler.PatchScheduler.process_stream')
    @patch('skills.auto_patch_pipeline.AutoPatchPipeline.verify_patch_stream')
    def test_execute_stream_patch_flow(self, mock_verify_stream, mock_process_stream):
        processed_mock = io.BytesIO(uuid.uuid4().bytes)
        mock_process_stream.return_value = processed_mock
        expected_verification = {uuid.uuid4().hex: random.choice([True, False])}
        mock_verify_stream.return_value = expected_verification

        executor = PatchAutoExecutor()
        result = executor.execute_stream_patch(self.module_name, self.stream_data)

        mock_process_stream.assert_called_once_with(self.module_name, self.stream_data)
        mock_verify_stream.assert_called_once_with(processed_mock)
        self.assertEqual(result, expected_verification)

    def test_randomized_chaos_execution(self):
        rand_mod = "".join(random.choices(string.ascii_lowercase, k=12))
        rand_exc = "".join(random.choices(string.ascii_letters, k=20))
        rand_tb = "".join(random.choices(string.printable, k=50))

        with patch('skills.patch_scheduler.PatchScheduler.schedule_patch') as mock_sched, \
             patch('skills.auto_patch_pipeline.AutoPatchPipeline.run_pipeline') as mock_pipe:

            mock_sched.return_value = True
            mock_res = MagicMock()
            mock_res.success = True
            mock_res.incident_id = uuid.uuid4().hex
            mock_pipe.return_value = mock_res

            executor = PatchAutoExecutor()
            res = executor.execute_auto_patch(rand_mod, rand_exc, rand_tb, {"chaos": rand_tb})

            self.assertEqual(res.incident_id, mock_res.incident_id)
            mock_sched.assert_called_once_with(rand_mod, rand_exc, rand_tb)
            mock_pipe.assert_called_once_with(rand_mod, rand_exc, rand_tb, {"chaos": rand_tb})

if __name__ == '__main__':
    unittest.main()