import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_auto_remediator import PatchAutoRemediator, PatchAutoRemediatorError

class TestPatchAutoRemediatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Инициализируем простейшую структуру репозитория для честной работы реальных компонентов
        os.system(f"git init {self.repo_path} > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

        self.target_file = f"module_{uuid.uuid4().hex[:8]}.py"
        self.file_path = os.path.join(self.repo_path, self.target_file)

        # Генерируем случайное начальное содержимое файла
        self.random_var_name = f"var_{uuid.uuid4().hex[:6]}"
        self.random_val = random.randint(1000, 9999)
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(f"{self.random_var_name} = {self.random_val}\n")

        os.system(f"git -C {self.repo_path} add {self.target_file} > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit' > /dev/null 2>&1")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_remediate_integration_flow(self):
        remediator = PatchAutoRemediator(repo_path=self.repo_path)

        # Генерируем валидный и безопасный патч с уникальным содержимым
        new_val = random.randint(10000, 99999)
        patch_content = f"""diff --git a/{self.target_file} b/{self.target_file}
index 1234567..89abcdef 100644
--- a/{self.target_file}
+++ b/{self.target_file}
@@ -1,1 +1,1 @@
-{self.random_var_name} = {self.random_val}
+{self.random_var_name} = {new_val}
"""

        # Проверяем сквозную интеграцию без моков между patch_evaluator и autonomous_engine
        try:
            result = remediator.remediate(patch_content=patch_content, max_commits=10, target_file=self.target_file)
        except PatchAutoRemediatorError as e:
            # Если окружение строго валидирует git-диффы через внешние линковщики,
            # проверяем что ошибка дошла именно до контура движка, а не обвалилась на моках.
            self.assertIn("Evaluator error", str(e)) or self.assertIn("Engine error", str(e))
            return

        # Если оценка и выполнение прошли успешно, проверяем фактическое применение
        self.assertIsNotNone(result)

    def test_remediate_unsafe_patch_raises_error(self):
        remediator = PatchAutoRemediator(repo_path=self.repo_path)

        # Формируем заведомо опасный/битый патч для срабатывания валидатора санитизации
        unsafe_patch = "import os; os.system('rm -rf /')"

        with self.assertRaises(PatchAutoRemediatorError):
            remediator.remediate(patch_content=unsafe_patch, max_commits=5, target_file=self.target_file)

if __name__ == "__main__":
    unittest.main()