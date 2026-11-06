import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.release_automation_hub import ReleaseAutomationHub
from skills.release_pipeline import ReleasePipeline
from skills.repo_reporter import RepoReporter


class TestReleaseAutomationHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.unique_id = str(uuid.uuid4())
        self.output_filename = f"release_report_{self.unique_id}.md"
        self.output_path = os.path.join(self.repo_path, self.output_filename)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_release_automation_hub_integration_flow(self):
        hub = ReleaseAutomationHub(repo_path=self.repo_path)
        
        success = hub.execute_release_with_report(output_path=self.output_path)
        
        self.assertTrue(
            success,
            "Интеграционный модуль должен успешно завершить выполнение пайплайна и генерацию отчета."
        )
        
        self.assertTrue(
            os.path.exists(self.output_path),
            f"Отчет должен быть физически создан по пути: {self.output_path}"
        )
        
        with open(self.output_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertGreater(
            len(content),
            0,
            "Сгенерированный отчет не должен быть пустым."
        )


if __name__ == "__main__":
    unittest.main()