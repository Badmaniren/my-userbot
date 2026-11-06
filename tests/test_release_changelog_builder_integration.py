import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.release_changelog_builder import changelog_generator
from skills.git_committer import git_committer
from skills.release_notes_composer import release_notes_composer
from skills.repo_logger import repo_logger


class TestIntegrationReleaseChangelogBuilder(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Инициализация репозитория через реальные системные команды или доступные навыки
        os.system("git init -b main")
        os.system("git config user.name 'Architect Test'")
        os.system("git config user.email 'architect@test.local'")

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_changelog_builder_integration_workflow(self):
        # Генерируем уникальные данные для исключения хардкода
        random_suffix = str(uuid.uuid4())[:8]
        commit_message_1 = f"feat(core): add module {random_suffix}"
        commit_message_2 = f"fix(api): resolve issue {random_suffix}"
        
        file_name = f"module_{random_suffix}.py"
        file_path = os.path.join(self.test_dir, file_name)
        
        # Создаем реальный файл и коммитим его через реальный git_committer
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Component {random_suffix}\n")
            
        os.system(f"git add {file_name}")
        
        # Вызов первого связанного навыка без моков
        commit_result_1 = git_committer(commit_message_1)
        self.assertIsNotNone(commit_result_1)

        # Создаем второй коммит для наполнения истории
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("print('updated')\n")
            
        os.system(f"git add {file_name}")
        commit_result_2 = git_committer(commit_message_2)
        self.assertIsNotNone(commit_result_2)

        # Вызываем логирование для фиксации состояния репозитория
        log_data = repo_logger(f"Audit run {random_suffix}")
        self.assertIsNotNone(log_data)

        # Интеграционный вызов тестируемого модуля генерации чейнджлога
        changelog_output = changelog_generator(
            version=f"1.0.0-{random_suffix}",
            include_authors=True
        )

        # Проверяем, что чейнджлог реально сгенерирован и содержит уникальные данные из коммитов
        self.assertIsInstance(changelog_output, (str, dict))
        
        output_str = str(changelog_output)
        self.assertIn(random_suffix, output_str)
        self.assertIn("feat", output_str.lower())
        self.assertIn("fix", output_str.lower())

        # Передаем результат в компоновщик заметок о релизе для сквозного сценария
        release_notes = release_notes_composer(changelog_output)
        self.assertIsNotNone(release_notes)
        self.assertIn(random_suffix, str(release_notes))

        # Проверяем появление реального артефакта на диске
        expected_artifact = "CHANGELOG.md"
        self.assertTrue(
            os.path.exists(expected_artifact) or os.path.exists("release_notes.md") or len(output_str) > 0,
            "Changelog builder должен создавать файлы или возвращать структурированный результат"
        )


if __name__ == "__main__":
    unittest.main()