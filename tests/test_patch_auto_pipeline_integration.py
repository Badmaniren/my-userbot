import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_auto_pipeline import PatchAutoPipeline, PatchAutoPipelineError
from skills.patch_evaluator import PatchEvaluator
from skills.patch_verifier import PatchVerifier


class TestPatchAutoPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.target_filename = f"module_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_filename)

        self.initial_content = f"# Initial code {uuid.uuid4()}\n\ndef compute():\n    return {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        self.random_val = random.randint(101, 999)
        self.patch_content = f"def compute():\n    return {self.random_val}\n"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_integration_success(self):
        pipeline = PatchAutoPipeline(repo_path=self.repo_path)

        result = pipeline.run_pipeline(
            patch_content=self.patch_content,
            target_file=self.target_filename
        )

        self.assertTrue(
            result,
            "Интеграционный конвейер должен успешно обработать, оценить и верифицировать безопасный патч."
        )

        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(
            str(self.random_val),
            updated_content,
            "Файл должен содержать изменения из примененного и верифицированного патча."
        )

    def test_pipeline_integration_failure_unsafe_patch(self):
        pipeline = PatchAutoPipeline(repo_path=self.repo_path)

        unsafe_keyword = f"os.system('rm -rf / # {uuid.uuid4().hex}')"
        unsafe_patch = f"def compute():\n    {unsafe_keyword}\n    return 0\n"

        with self.assertRaises((PatchAutoPipelineError, Exception)):
            pipeline.run_pipeline(
                patch_content=unsafe_patch,
                target_file=self.target_filename
            )

        with open(self.target_file_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        self.assertEqual(
            current_content,
            self.initial_content,
            "При отклонении небезопасного патча конвейером исходный файл не должен изменяться."
        )


if __name__ == "__main__":
    unittest.main()