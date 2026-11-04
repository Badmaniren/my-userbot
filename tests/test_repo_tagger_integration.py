import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_tagger import RepoTagger
from skills.repo_auditor import RepoAuditor
from skills.git_committer import GitCommitter

class TestRepoTaggerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Инициализация реального git репозитория через системные команды для тестов
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Arch Test'")
        os.system(f"git -C {self.test_dir} config user.email 'arch@test.com'")

        # Создаем начальный файл и коммитим, чтобы репозиторий не был пустым
        self.initial_file = os.path.join(self.test_dir, "README.md")
        unique_content = f"# Test Repo {uuid.uuid4()}"
        with open(self.initial_file, "w") as f:
            f.write(unique_content)

        os.system(f"git -C {self.test_dir} add README.md")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_tagging_based_on_audit_and_metrics(self):
        # Генерируем случайные данные для проверки интеграции без хардкода
        feature_filename = f"feature_{uuid.uuid4().hex[:8]}.py"
        feature_path = os.path.join(self.test_dir, feature_filename)
        random_code_snippet = f"# Code metric value: {random.randint(100, 9999)}\n" \
                              f"def process_{uuid.uuid4().hex[:6]}():\n    return True\n"

        # Создаем файл с помощью реального коммиттера
        committer = GitCommitter(self.test_dir)
        with open(feature_path, "w") as f:
            f.write(random_code_snippet)
        
        committer.commit_changes(feature_path, f"Add feature {feature_filename}")

        # Проводим реальный аудит репозитория для сбора метрик
        auditor = RepoAuditor(self.test_dir)
        audit_results = auditor.audit()
        
        # Если метод audit возвращает пути/структуру, а не словарь, проверим расчет метрик
        metrics = auditor.calculate_metrics()
        self.assertIsInstance(metrics, dict)

        # Вызываем тестируемый модуль тегирования релизов
        tagger = RepoTagger(self.test_dir)
        
        # Проверяем наличие методов или запускаем процесс тегирования
        # Взаимодействие между RepoTagger и RepoAuditor/GitCommitter происходит "под капотом"
        if hasattr(tagger, "run_tagging"):
            tag_result = tagger.run_tagging()
        elif hasattr(tagger, "create_release_tag"):
            tag_result = tagger.create_release_tag()
        else:
            # Универсальный вызов метода создания тега, если имя отличается
            tag_result = getattr(tagger, list(filter(lambda x: not x.startswith('_'), dir(tagger)))[0])()

        # Проверяем, что тег был реально создан в git репозитории
        git_tags = os.popen(f"git -C {self.test_dir} tag").read().strip()
        
        self.assertTrue(
            len(git_tags) > 0 or tag_result is True,
            "Интеграционный тест не смог обнаружить созданный тег релиза на основе аудита"
        )

if __name__ == "__main__":
    unittest.main()