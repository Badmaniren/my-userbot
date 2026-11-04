import unittest
import os
import tempfile
import shutil
import zipfile
import uuid
import random
from skills.repo_release_exporter import RepoReleaseExporter


class TestRepoReleaseExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация минимального git-репозитория для корректной работы зависимых навыков (tagger, pipeline)
        os.system(f"git init {self.repo_path} > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Создаем случайный файл, чтобы в репозитории были изменения для коммита/тегирования
        self.random_filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        self.random_file_path = os.path.join(self.repo_path, self.random_filename)
        self.random_content = f"Random content: {random.randint(1, 100000)}"
        
        with open(self.random_file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content)
            
        os.system(f"git -C {self.repo_path} add {self.random_filename} > /dev/null 2>&1")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit' > /dev/null 2>&1")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_release_integration_with_real_dependencies(self):
        exporter = RepoReleaseExporter(self.repo_path)
        
        random_tag = f"v1.{random.randint(0, 99)}.{random.randint(0, 99)}"
        dest_folder = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex[:6]}")
        
        result = exporter.export_release(tag=random_tag, dest_path=dest_folder)
        
        self.assertTrue(result, "Экспорт релиза должен завершиться успешно без моков.")
        
        extracted_file_path = os.path.join(dest_folder, self.random_filename)
        self.assertTrue(os.path.exists(extracted_file_path), "Распакованный архив должен содержать исходные файлы репозитория.")
        
        with open(extracted_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertEqual(content, self.random_content, "Содержимое файла в распакованном архиве должно совпадать с оригиналом.")

    def test_batch_export_from_stream_integration(self):
        exporter = RepoReleaseExporter(self.repo_path)
        
        stream_data = f"audit_stream_data_{uuid.uuid4().hex}"
        stream_result = exporter.batch_export_from_stream(stream_data)
        
        self.assertIsNotNone(stream_result, "Метод batch_export_from_stream должен возвращать результат обработки потока.")


if __name__ == "__main__":
    unittest.main()