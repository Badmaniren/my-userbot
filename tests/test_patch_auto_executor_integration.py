import unittest
import uuid
import random
import sys
import os

from skills.patch_auto_executor import PatchAutoExecutor

class TestPatchAutoExecutorIntegration(unittest.TestCase):
    def setUp(self):
        self.executor = PatchAutoExecutor()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.error_message = f"RandomError_{uuid.uuid4().hex[:6]}"
        self.exception = RuntimeError(self.error_message)
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}, in <module>\n    raise RuntimeError('{self.error_message}')"
        self.context = {"env": "integration_test", "run_id": random.randint(1000, 9999)}

    def test_full_auto_execution_and_recovery_pipeline(self):
        result = self.executor.execute_and_patch(
            module_name=self.module_name,
            exception=self.exception,
            traceback_str=self.traceback_str,
            context=self.context
        )

        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'success'))
        self.assertTrue(hasattr(result, 'incident_id'))
        self.assertTrue(hasattr(result, 'patch_data'))
        
        self.assertIsInstance(result.incident_id, str)
        self.assertTrue(len(result.incident_id) > 0)

        stream_data = {
            "module": self.module_name,
            "stream_id": str(uuid.uuid4()),
            "status": "failed"
        }
        
        verification = self.executor.verify_and_execute_stream(stream_data)
        self.assertIsNotNone(verification)

if __name__ == '__main__':
    unittest.main()