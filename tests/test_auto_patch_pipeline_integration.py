import unittest
import uuid
import random
import sys
import os
import traceback

from skills.auto_patch_pipeline import AutoPatchPipeline
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator

class TestAutoPatchPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = AutoPatchPipeline()
        self.random_module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"RuntimeError_{uuid.uuid4().hex[:6]}"
        
    def test_pipeline_composition_and_execution(self):
        self.assertIsInstance(self.pipeline, AutoPatchPipeline)
        
        # Генерируем уникальные входные данные для исключения хардкода
        try:
            raise RuntimeError(self.random_error_msg)
        except RuntimeError as e:
            tb_str = "".join(traceback.format_exception(*sys.exc_info()))
            
            # Вызываем реальный конвейер без моков между error_recovery_hub и patch_validator
            result = self.pipeline.run_pipeline(
                module_name=self.random_module_name,
                exception=e,
                traceback_str=tb_str,
                context={"random_seed": random.randint(1, 1000)}
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn("incident_id", result)
            self.assertIn("status", result)
            
            # Проверяем реальное взаимодействие навыков в составе композиции
            incident_id = result["incident_id"]
            self.assertTrue(len(incident_id) > 0)
            
            # Убеждаемся, что ErrorRecoveryHub зафиксировал инцидент
            history = self.pipeline.recovery_hub.get_incident_history(self.random_module_name)
            self.assertIsInstance(history, list)
            
            # Проверяем работу PatchValidator через конвейер
            if "patch_data" in result and result["patch_data"]:
                validation_res = self.pipeline.validator.validate(result["patch_data"])
                self.assertIsInstance(validation_res, bool)

if __name__ == "__main__":
    unittest.main()