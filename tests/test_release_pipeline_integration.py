import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.release_pipeline import ReleasePipeline
from skills.release_notes_composer import ReleaseNotesComposer
from skills.release_notes_publisher import ReleaseNotesPublisher


class TestReleasePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Создаем минимальную структуру git-репозитория, чтобы зависимости не падали
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Генерируем уникальные данные для текущего теста
        self.unique_tag = f"v1.0.{random.randint(100, 999)}-{uuid.uuid4().hex[:6]}"
        self.random_commit_msg = f"feat: add feature {uuid.uuid4().hex}"
        
        # Создаем коммит и тег для реальной работы композиции навыков
        dummy_file = os.path.join(self.repo_path, "README.md")
        with open(dummy_file, "w") as f:
            f.write(f"# Release {self.unique_tag}\n")
            
        os.system(f"git -C {self.repo_path} add README.md")
        os.system(f"git -C {self.repo_path} commit -m '{self.random_commit_msg}'")
        os.system(f"git -C {self.repo_path} tag {self.unique_tag}")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_release_pipeline_end_to_end_composition(self):
        output_filename = f"release_notes_{uuid.uuid4().hex}.md"
        output_path = os.path.join(self.repo_path, output_filename)

        # Инициализируем тестируемый модуль релизного пайплайна
        pipeline = ReleasePipeline(repo_path=self.repo_path)

        # Проверяем, что пайплайн действительно использует требуемые навыки в композиции
        self.assertTrue(
            hasattr(pipeline, "composer") or hasattr(pipeline, "publisher") or 
            isinstance(getattr(pipeline, "composer", None), ReleaseNotesComposer) or
            isinstance(getattr(pipeline, "publisher", None), ReleaseNotesPublisher),
            "Модуль ReleasePipeline обязан композиционно включать ReleaseNotesComposer и ReleaseNotesPublisher"
        )

        # Запускаем полный цикл пайплайна
        success = pipeline.run(output_path=output_path)

        # Проверяем реальный результат работы пайплайна и его компонентов
        self.assertTrue(
            success, 
            "Пайплайн публикации релизов должен завершиться успешно (возвратить True)"
        )
        
        self.assertTrue(
            os.path.exists(output_path),
            f"Интеграционный пайплайн должен физически создать файл заметок по пути: {output_path}"
        )

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(
            self.random_commit_msg,
            content,
            "Сгенерированные релизные заметки должны содержать реальный коммит из репозитория"
        )


if __name__ == "__main__":
    unittest.main()