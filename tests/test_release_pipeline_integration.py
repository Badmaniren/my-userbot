import unittest
import tempfile
import os
import uuid
from skills.release_pipeline import ReleasePipeline


class TestReleasePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_release_pipeline_real_integration(self):
        pipeline = ReleasePipeline(repo_path=self.repo_path)

        unique_filename = f"release_{uuid.uuid4()}.md"
        output_path = os.path.join(self.repo_path, unique_filename)

        success = pipeline.run(output_path=output_path)

        self.assertTrue(success, "Пайплайн релиза должен вернуть True при успешном выполнении.")
        self.assertTrue(
            os.path.exists(output_path),
            f"Артефакт релиза должен быть реально сохранен по пути: {output_path}"
        )
        
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIsNotNone(content, "Содержимое файла релиза не должно быть пустым.")


if __name__ == "__main__":
    unittest.main()