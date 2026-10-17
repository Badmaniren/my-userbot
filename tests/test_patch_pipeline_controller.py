import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.patch_pipeline_controller import (
    PatchPipelineController,
    PatchPipelineControllerError
)
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluatorError
from skills.patch_verifier import PatchExecutorError


class TestPatchPipelineController(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_content = "".join(random.choices(string.ascii_letters + string.whitespace, k=64))
        self.target_file = f"{uuid.uuid4().hex}.py"

    def test_controller_initialization_success(self):
        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier") as mock_verifier_cls:
            
            controller = PatchPipelineController(self.repo_path)
            
            self.assertEqual(controller.repo_path, self.repo_path)
            mock_evaluator_cls.assert_called_once_with(self.repo_path)
            mock_verifier_cls.assert_called_once()

    def test_process_pipeline_success(self):
        evaluation_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={uuid.uuid4().hex: random.randint(1, 100)},
            reasons=[],
            telemetry={uuid.uuid4().hex: uuid.uuid4().hex},
            was_corrected=False
        )

        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier") as mock_verifier_cls:
            
            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluator.evaluate.return_value = evaluation_result

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify_and_apply.return_value = True

            controller = PatchPipelineController(self.repo_path)
            result = controller.process(self.patch_content, self.target_file)

            self.assertTrue(result)
            mock_evaluator.evaluate.assert_called_once_with(
                patch_content=self.patch_content,
                collect_telemetry=True,
                target_file=self.target_file
            )
            mock_verifier.verify_and_apply.assert_called_once_with(self.patch_content)

    def test_process_pipeline_evaluation_unsafe(self):
        evaluation_result = PatchEvaluationResult(
            is_safe=False,
            is_valid=True,
            metrics={},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=False
        )

        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier") as mock_verifier_cls:
            
            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluator.evaluate.return_value = evaluation_result

            mock_verifier = mock_verifier_cls.return_value

            controller = PatchPipelineController(self.repo_path)
            result = controller.process(self.patch_content, self.target_file)

            self.assertFalse(result)
            mock_evaluator.evaluate.assert_called_once()
            mock_verifier.verify_and_apply.assert_not_called()

    def test_process_pipeline_evaluation_invalid(self):
        evaluation_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=False,
            metrics={},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=False
        )

        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier") as mock_verifier_cls:
            
            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluator.evaluate.return_value = evaluation_result

            mock_verifier = mock_verifier_cls.return_value

            controller = PatchPipelineController(self.repo_path)
            result = controller.process(self.patch_content, self.target_file)

            self.assertFalse(result)
            mock_evaluator.evaluate.assert_called_once()
            mock_verifier.verify_and_apply.assert_not_called()

    def test_process_pipeline_evaluator_raises_exception(self):
        err_msg = uuid.uuid4().hex
        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier"):
            
            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluator.evaluate.side_effect = PatchEvaluatorError(err_msg)

            controller = PatchPipelineController(self.repo_path)
            
            with self.assertRaises(PatchPipelineControllerError) as ctx:
                controller.process(self.patch_content, self.target_file)
            
            self.assertIn(err_msg, str(ctx.exception))

    def test_process_pipeline_verifier_raises_exception(self):
        evaluation_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        err_msg = uuid.uuid4().hex

        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier") as mock_verifier_cls:
            
            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluator.evaluate.return_value = evaluation_result

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify_and_apply.side_effect = PatchExecutorError(err_msg)

            controller = PatchPipelineController(self.repo_path)
            
            with self.assertRaises(PatchPipelineControllerError) as ctx:
                controller.process(self.patch_content, self.target_file)
            
            self.assertIn(err_msg, str(ctx.exception))

    def test_evaluate_and_autocorrect_flow(self):
        evaluation_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=True
        )

        with patch("skills.patch_pipeline_controller.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_pipeline_controller.PatchVerifier") as mock_verifier_cls:
            
            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluator.evaluate_with_autocorrect.return_value = evaluation_result

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify_and_apply.return_value = True

            controller = PatchPipelineController(self.repo_path)
            result = controller.process_with_autocorrect(self.patch_content)

            self.assertTrue(result)
            mock_evaluator.evaluate_with_autocorrect.assert_called_once_with(self.patch_content)
            mock_verifier.verify_and_apply.assert_called_once_with(self.patch_content)


if __name__ == "__main__":
    unittest.main()