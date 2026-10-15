import unittest
import os
import tempfile
import shutil
import uuid
from skills.patch_executor import PatchExecutor, PatchExecutorError
from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector


class TestPatchExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Инициализация реального git репозитория в временной директории для интеграционного теста
        os.system(f"git -C {self.repo_path} init -q")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        
        # Создаем начальный файл и коммитим, чтобы у GitInspector была история
        self.initial_filename = f"test_{uuid.uuid4().hex}.txt"
        self.initial_filepath = os.path.join(self.repo_path, self.initial_filename)
        self.initial_content = f"initial content {uuid.uuid4()}"

        with open(self.initial_filepath, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        os.system(f"git -C {self.repo_path} add {self.initial_filename}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit' -q")

        # Получаем реальный хэш коммита
        import subprocess
        res = subprocess.run(["git", "-C", self.repo_path, "rev-parse", "HEAD"], capture_output=True, text=True)
        self.initial_commit_hash = res.stdout.strip()

        # Интеграция реальных навыков без моков
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.patch_executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_apply_and_rollback_patch(self):
        random_file_name = f"hypothesis_{uuid.uuid4().hex}.py"
        random_file_content = f"# Autonomous learning payload {uuid.uuid4()}"

        patch_data = {
            "file_path": random_file_name,
            "content": random_file_content
        }

        # Шаг 1: Применяем патч через реальный PatchExecutor
        applied = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(applied)

        target_full_path = os.path.join(self.repo_path, random_file_name)
        self.assertTrue(os.path.exists(target_full_path))

        with open(target_full_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_file_content)

        # Шаг 2: Откатываем патч используя интеграцию с GitInspector (файла не должно стать в начальном коммите)
        rolled_back = self.patch_executor.rollback_patch(random_file_name, self.initial_commit_hash)
        self.assertTrue(rolled_back)
        self.assertFalse(os.path.exists(target_full_path))

    def test_integration_execute_from_lessons_anti_cheat(self):
        random_lesson_id = f"lesson_{uuid.uuid4().hex}"
        random_patch_path = f"modules/{uuid.uuid4().hex}.py"
        random_patch_content = f"print('{uuid.uuid4()}')"

        # Создаем структуру урока в репозитории, которую LessonParser реально должен прочитать
        lessons_dir = os.path.join(self.repo_path, "lessons")
        os.makedirs(lessons_dir, exist_ok=True)

        lesson_file_path = os.path.join(lessons_dir, f"{random_lesson_id}.md")
        lesson_markdown = f"""
# Lesson ID: {random_lesson_id}
# file_path: {random_patch_path}
{random_patch_content}
"""
        with open(lesson_file_path, "w", encoding="utf-8") as f:
            f.write(lesson_markdown)

        os.system(f"git -C {self.repo_path} add lessons/")
        os.system(f"git -C {self.repo_path} commit -m 'Add lesson {random_lesson_id}' -q")

        # Выполняем цепочку execute_from_lessons без моков
        execution_results = self.patch_executor.execute_from_lessons()

        self.assertIsInstance(execution_results, dict)

        # Проверяем реальное появление файла патча на диске
        applied_file_full_path = os.path.join(self.repo_path, random_patch_path)
        self.assertTrue(os.path.exists(applied_file_full_path))

        with open(applied_file_full_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(random_patch_content, content)


if __name__ == "__main__":
    unittest.main()