import unittest
import tempfile
import os
import uuid
from skills.release_pipeline import ReleasePipeline


class TestReleasePipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        # Инициализируем минимальную git-среду для работы компоновщика и издателя
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Создаем начальный коммит, чтобы было что анализировать
        self.dummy_file = os.path.join(self.repo_path, "README.md")
        random_content = f"Initial commit {uuid.uuid4()}"
        with open(self.dummy_file, "w") as f:
            f.write(random_content)
            
        os.system(f"git -C {self.repo_path} add README.md")
        os.system(f"git -C {self.repo_path} commit -m 'feat: initial setup'")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_release_pipeline_integration(self):
        # Генерируем уникальное имя файла для отчета, исключая хардкод
        unique_filename = f"release_report_{uuid.uuid4()}.md"
        output_path = os.path.join(self.repo_path, unique_filename)

        pipeline = ReleasePipeline(repo_path=self.repo_path)
        
        # Выполняем реальный интеграционный проход без моков между компонентами
        success = pipeline.run(output_path=output_path)

        # Проверяем контракт выполнения пайплайна
        self.assertTrue(success, "Пайплайн релиза должен завершиться успешно")
        
        # Проверяем реальное появление сгенерированного файла отчета на диске
        self.assertTrue(
            os.path.exists(output_path),
            f"Файл релиза должен быть создан по пути {output_path}"
        )
        
        # Проверяем, что файл содержит данные, а не является пустым
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(
                len(content), 0, "Экспортированный файл отчета не должен быть пустым"
            )


if __name__ == "__main__":
    unittest.main()