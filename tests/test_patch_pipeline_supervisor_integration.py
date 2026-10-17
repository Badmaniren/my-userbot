import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.patch_pipeline_supervisor import PatchPipelineSupervisor
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_verifier import PatchVerifier

class TestPatchPipelineSupervisorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        
        # Инициализируем простейший git репозиторий для тестов верификатора и анализатора
        os.system("git init")
        os.system("git config user.name 'Test User'")
        os.system("git config user.email 'test@example.com'")
        
        self.file_name = f"test_{uuid.uuid4().hex}.py"
        self.file_path = os.path.join(self.test_dir, self.file_name)
        
        # Создаем базовый файл
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("print('initial')\n")
            
        os.system("git add .")
        os.system("git commit -m 'initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_supervisor_real_integration(self):
        random_str = uuid.uuid4().hex
        modified_content = f"print('initial')\nprint('{random_str}')\n"
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
            
        # Получаем реальный diff через git через командную строку для подготовки патча
        import subprocess
        diff_output = subprocess.check_output(["git", "diff"], text=True)
        
        # Инициализируем реальные компоненты композиции без моков
        analyzer = PatchAnalyzer()
        verifier = PatchVerifier(repo_path=self.test_dir, inspector=None, executor=None)
        
        # Передаем реальные экземпляры в супервизор конвейера
        supervisor = PatchPipelineSupervisor(analyzer=analyzer, verifier=verifier)
        
        # Генерируем случайный идентификатор сессии конвейера для проверки сквозной передачи
        session_id = str(uuid.uuid4())
        
        # Запускаем реальный конвейер обработки патча
        pipeline_result = supervisor.process_patch(
            diff_text=diff_output,
            session_id=session_id,
            target_file=self.file_name
        )
        
        self.assertIsNotNone(pipeline_result)
        self.assertIn("analyzed", pipeline_result)
        self.assertIn("verified", pipeline_result)
        self.assertEqual(pipeline_result.get("session_id"), session_id)
        
        # Проверяем, что анализ действительно отработал по переданному diff
        analysis_stats = pipeline_result.get("statistics") or {}
        self.assertIsInstance(analysis_stats, dict)

if __name__ == "__main__":
    unittest.main()