import unittest
import uuid
import random
import os
import tempfile
import subprocess
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError, GitInspector


class TestPatchAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        # Инициализируем реальный git репозиторий для интеграционной проверки GitInspector и PatchAnalyzer
        subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "architect@test.com"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Architect"], cwd=self.repo_path, capture_output=True, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_git_and_patch_analyzer(self):
        # Генерируем уникальные данные для теста, исключая хардкод
        unique_file_name = f"file_{uuid.uuid4().hex[:8]}.py"
        file_path = os.path.join(self.repo_path, unique_file_name)

        random_code_line = f"print('{uuid.uuid4()}')"

        # Создаем файл в репозитории
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("def initial():\n    pass\n")

        subprocess.run(["git", "add", unique_file_name], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, capture_output=True, check=True)

        # Вносим изменения в файл
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"def initial():\n    {random_code_line}\n    return True\n")

        subprocess.run(["git", "add", unique_file_name], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Update commit"], cwd=self.repo_path, capture_output=True, check=True)

        # Получаем хэш последнего коммита
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True, check=True)
        commit_hash = res.stdout.strip()

        # Интегрируем GitInspector и PatchAnalyzer без моков
        inspector = GitInspector(self.repo_path)
        diff_text = inspector.get_file_diff(commit_hash)

        # Выполняем анализ реального diff
        analysis_result = self.analyzer.analyze(diff_text)

        self.assertTrue(analysis_result["is_valid"])
        self.assertIn(unique_file_name, analysis_result["files"])
        self.assertGreater(analysis_result["additions"], 0)

        # Проверяем работу stream и file анализаторов
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
            tmp.write(diff_text)
            tmp_name = tmp.name

        try:
            file_analysis = self.analyzer.analyze_file(tmp_name)
            self.assertTrue(file_analysis["is_valid"])
            self.assertEqual(file_analysis["additions"], analysis_result["additions"])

            with open(tmp_name, "r", encoding="utf-8") as stream_f:
                stream_analysis = self.analyzer.analyze_stream(stream_f)
                self.assertTrue(stream_analysis["is_valid"])
                self.assertEqual(stream_analysis["deletions"], analysis_result["deletions"])
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_integration_syntax_risks_and_validation(self):
        # Генерируем случайную опасную конструкцию и случайный uuid
        random_var = f"var_{uuid.uuid4().hex[:6]}"
        malicious_diff = f"""--- a/test_risk.py
+++ b/test_risk.py
@@ -1,1 +1,1 @@
-print("old")
+{random_var} = eval("1 + 1")
"""

        analysis = self.analyzer.analyze(malicious_diff)
        self.assertTrue(analysis["is_valid"])

        risk_detected = False
        for risk in analysis["risks"]:
            if risk["type"] == "dangerous_call" and "eval" in risk["details"]:
                risk_detected = True

        self.assertTrue(risk_detected, "Integrational check failed to detect dynamically injected eval risk")

    def test_integration_invalid_diff_raises_error(self):
        garbage_data = f"random_garbage_{uuid.uuid4()}"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(garbage_data)

        result = self.analyzer.analyze(garbage_data)
        self.assertFalse(result["is_valid"])
        self.assertTrue(len(result["errors"]) > 0)


if __name__ == "__main__":
    unittest.main()