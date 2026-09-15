import unittest
import uuid
import random
from skills.package_dependency_resolver import (
    pypi_client,
    patch_validator,
    error_recovery_hub,
    auto_patch_pipeline
)

class TestPackageDependencyResolverIntegration(unittest.TestCase):

    def setUp(self):
        self.random_str = str(uuid.uuid4())
        self.package_name = f"pkg-{self.random_str[:8]}"
        self.version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.client = pypi_client.PyPIClient()
        self.validator = patch_validator.PatchValidator()
        self.hub = error_recovery_hub.ErrorRecoveryHub()
        self.pipeline = auto_patch_pipeline.AutoPatchPipeline()

    def test_dependency_resolution_and_recovery_flow(self):
        # 1. Проверяем взаимодействие с pypi_client для получения зависимостей
        versions = self.client.get_release_versions(self.package_name)
        self.assertIsInstance(versions, list)

        metadata = self.client.get_package_metadata(self.package_name, self.version)
        self.assertIsInstance(metadata, dict)

        dependencies = self.client.get_dependencies(self.package_name, self.version)
        self.assertIsInstance(dependencies, list)

        # 2. Валидация сгенерированного патча через patch_validator
        test_code = f"def dynamic_fix_{self.random_str[:8]}():\n    return '{self.random_str}'"
        static_analysis = self.validator.analyze_static(test_code)
        self.assertIsInstance(static_analysis, dict)

        is_valid = self.validator.validate({"code": test_code, "id": self.random_str})
        self.assertIsInstance(is_valid, bool)

        # 3. Инцидент и пайфлайн восстановления через error_recovery_hub и auto_patch_pipeline
        exc = RuntimeError(f"Dependency error: {self.random_str}")
        tb = f"Traceback (most recent call last):\n  File '{self.random_str}.py', line 1, in <module>\n    raise Exception"
        
        incident_id = self.hub.capture_failure(self.package_name, exc, tb)
        self.assertIsNotNone(incident_id)

        history = self.hub.get_incident_history(self.package_name)
        self.assertIsInstance(history, list)

        logs = self.hub.get_incident_logs(incident_id)
        self.assertIsInstance(logs, dict)

        pipeline_result = self.pipeline.run_pipeline(
            module_name=self.package_name,
            exception=exc,
            traceback_str=tb,
            context={"run_id": self.random_str}
        )
        
        self.assertIsInstance(pipeline_result, auto_patch_pipeline.PipelineResult)
        self.assertEqual(pipeline_result.incident_id, incident_id)

    def test_force_analyze_and_recover_integration(self):
        exc = ValueError(f"Compatibility mismatch: {self.random_str}")
        result = self.pipeline.force_analyze_and_recover(
            module_name=self.package_name,
            exception=exc,
            context={"uuid": self.random_str}
        )
        
        self.assertIsInstance(result, auto_patch_pipeline.PipelineResult)
        self.assertIsNotNone(result.incident_id)
        
        logs = self.hub.get_incident_logs(result.incident_id)
        self.assertIsInstance(logs, dict)

if __name__ == "__main__":
    unittest.main()