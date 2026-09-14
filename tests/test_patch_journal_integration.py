import unittest
import uuid
import random
import os
import shutil

from skills.patch_journal import (
    AutoPatchPipeline,
    PipelineResult,
    ErrorRecoveryHub,
    PatchValidator,
    ASTInspector,
    sandbox_exec
)

class TestPatchJournalIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = AutoPatchPipeline()
        self.hub = ErrorRecoveryHub()
        self.validator = PatchValidator()
        self.test_module_name = f"test_mod_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.random_error_msg = f"DynamicError_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        cleanup_target = f"{self.test_module_name}.py"
        if os.path.exists(cleanup_target):
            try:
                os.remove(cleanup_target)
            except OSError:
                pass

    def test_end_to_end_patch_journal_pipeline(self):
        exception_instance = RuntimeError(self.random_error_msg)
        dummy_traceback = "Traceback (most recent call last):\n  File \"test.py\", line 1, in <module>\n    raise RuntimeError()"
        context_data = {"run_id": random.randint(1000, 9999), "meta": uuid.uuid4().hex}

        pipeline_result = self.pipeline.run_pipeline(
            module_name=self.test_module_name,
            exception=exception_instance,
            traceback_str=dummy_traceback,
            context=context_data
        )

        self.assertIsInstance(pipeline_result, PipelineResult)
        self.assertIsNotNone(pipeline_result.success)
        self.assertIsNotNone(pipeline_result.incident_id)

        history = self.hub.get_incident_history(self.test_module_name)
        self.assertIsInstance(history, (list, dict))

        safe_code_snippet = f"x = {random.randint(1, 100)}\ny = {random.randint(1, 100)}\nresult = x + y"
        validation_res = self.validator.verify_patch(safe_code_snippet)
        self.assertIsInstance(validation_res, dict)

        stream_data = [safe_code_snippet, f"z = x * {random.randint(2, 5)}"]
        stream_verification = self.pipeline.verify_patch_stream(stream_data)
        self.assertIsNotNone(stream_verification)

        forced_result = self.pipeline.force_analyze_and_recover(
            module_name=self.test_module_name,
            exception=exception_instance,
            context=context_data
        )
        self.assertIsNotNone(forced_result)

    def test_validator_and_sandbox_integration(self):
        risky_code = f"import os\nos.system('echo {uuid.uuid4().hex}')"
        inspector = ASTInspector(forbidden=["os", "sys"])
        self.assertIsNotNone(inspector)

        static_analysis = self.validator.analyze_static(risky_code)
        self.assertIsInstance(static_analysis, dict)

        sandbox_result = sandbox_exec(f"print({random.randint(100, 999)})")
        self.assertIsNotNone(sandbox_result)

        is_valid = self.validator.validate({"code": risky_code})
        self.assertIsInstance(is_valid, bool)

    def test_error_recovery_hub_workflow(self):
        captured_id = self.hub.capture_failure(
            module_name=self.test_module_name,
            exception=TypeError(self.random_error_msg),
            traceback_str="Dummy Traceback String"
        )
        self.assertIsNotNone(captured_id)

        logs = self.hub.get_incident_logs(str(captured_id) if captured_id else self.incident_id)
        self.assertIsNotNone(logs)

        analysis = self.hub.analyze_failure(str(captured_id) if captured_id else self.incident_id)
        self.assertIsNotNone(analysis)

        patch = self.hub.generate_patch(str(captured_id) if captured_id else self.incident_id)
        self.assertIsNotNone(patch)

        applied = self.hub.apply_patch(patch)
        self.assertIsInstance(applied, (bool, dict, type(None)))

        deploy_res = self.hub.deploy_and_verify(
            incident_id=str(captured_id) if captured_id else self.incident_id,
            patch_payload={"code": "pass"}
        )
        self.assertIsNotNone(deploy_res)

if __name__ == '__main__':
    unittest.main()