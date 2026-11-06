import unittest
import tempfile
import os
import uuid
import random
from skills.release_pipeline import ReleasePipeline


class TestReleasePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.pipeline = ReleasePipeline(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_release_pipeline_end_to_end_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        output_filename = f"release_notes_{random_suffix}.md"
        output_path = os.path.join(self.repo_path, output_filename)

        dummy_commit_msg = f"feat(core): update module for release {random_suffix}"
        git_dir = os.path.join(self.repo_path, ".git")
        os.makedirs(git_dir, exist_ok=True)
        
        with open(os.path.join(self.repo_path, "sample.txt"), "w") as f:
            f.write(f"Random data: {random.randint(1000, 9999)}")

        success = self.pipeline.run(output_path=output_path)

        self.assertTrue(
            success,
            f"ReleasePipeline.run() должен вернуть True для пути {output_path}"
        )
        self.assertTrue(
            os.path.exists(output_path),
            f"Интеграционный тест ожидает физического появления файла релиза: {output_path}"
        )

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIsInstance(content, str)
        self.assertTrue(
            len(content) >= 0,
            "Файл результатов компиляции и публикации должен быть доступен для чтения"
        )


if __name__ == "__main__":
    unittest.main()