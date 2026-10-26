import unittest
import uuid
import random
import tempfile
import os
import subprocess

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.git_inspector import GitInspector
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class TestPatchAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self.test_dir.name

        # Initialize a real git repository to test integration without mocks
        subprocess_run = lambda cmd: subprocess.run(cmd, cwd=self.repo_dir, capture_output=True, text=True, check=True)
        try:
            subprocess.run(["git", "init"], cwd=self.repo_dir, capture_output=True, text=True, check=True)
            subprocess.run(["git", "config", "user.name", "ArchitectBot"], cwd=self.repo_dir, capture_output=True, text=True, check=True)
            subprocess.run(["git", "config", "user.email", "bot@architect.test"], cwd=self.repo_dir, capture_output=True, text=True, check=True)
        except Exception:
            pass

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_analyzer_full_integration(self):
        # Генерируем случайные данные для исключения хардкода
        unique_marker = f"val_{uuid.uuid4().hex[:8]}"
        random_file_name = f"module_{uuid.uuid4().hex[:6]}.py"
        file_path = os.path.join(self.repo_dir, random_file_name)

        # Создаем базовый файл в репозитории
        initial_content = f"# Initial version\nprint('hello')\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        subprocess.run(["git", "add", random_file_name], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_dir, capture_output=True, check=True)

        # Модифицируем файл для получения реального диффа
        modified_content = f"# Initial version\nprint('{unique_marker}')\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

        subprocess.run(["git", "add", random_file_name], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Modify file"], cwd=self.repo_dir, capture_output=True, check=True)

        # Получаем хеш последнего коммита
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True, check=True)
        commit_hash = res.stdout.strip()

        # Интегрируем GitInspector и PatchAnalyzer напрямую без моков
        inspector = GitInspector(self.repo_dir)
        raw_diff = inspector.get_file_diff(commit_hash)

        self.assertIsInstance(raw_diff, str)
        self.assertTrue(len(raw_diff) > 0)

        analyzer = PatchAnalyzer()
        analysis_result = analyzer.analyze(raw_diff)

        # Проверяем структуру результата анализа
        self.assertTrue(analysis_result.get("is_valid"))
        self.assertIn(random_file_name, analysis_result.get("files", []))
        self.assertGreaterEqual(analysis_result.get("additions", 0), 1)

        # Проверяем логирование через AnomalyAuditHub для интеграционной цепочки
        log_file = os.path.join(self.repo_dir, f"audit_{uuid.uuid4().hex}.json")
        audit_hub = AnomalyAuditHub(repo_path=self.repo_dir, log_path=log_file, threshold=random.randint(1, 10))

        audit_hub.log_anomaly(
            source="patch_analyzer_integration",
            severity="INFO",
            details=f"Analyzed diff containing {unique_marker}",
            telemetry_snapshot={"commit": commit_hash, "files_changed": analysis_result["statistics"]["files_changed"]}
        )

        report = audit_hub.generate_final_report()
        self.assertIsNotNone(report)

if __name__ == "__main__":
    unittest.main()