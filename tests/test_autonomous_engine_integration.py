import unittest
import os
import shutil
import uuid
import random
from skills.autonomous_engine import AutonomousEngine
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor
from skills.patch_verifier import PatchVerifier

class TestAutonomousEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.abspath(f"test_repo_{uuid.uuid4().hex}")
        os.makedirs(self.test_dir, exist_ok=True)
        
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Bot'")
        os.system(f"git -C {self.test_dir} config user.email 'bot@test.com'")
        
        self.random_file_name = f"module_{uuid.uuid4().hex[:6]}.py"
        self.random_content = f"# id: {uuid.uuid4()}\nx = {random.randint(1, 100)}\n"
        
        file_path = os.path.join(self.test_dir, self.random_file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content)
            
        os.system(f"git -C {self.test_dir} add {self.random_file_name}")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit {uuid.uuid4()}'")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_autonomous_engine_full_loop(self):
        inspector = GitInspector(self.test_dir)
        parser = LessonParser(inspector)
        generator = HypothesisGenerator(inspector, parser)
        executor = PatchExecutor(self.test_dir, inspector, parser)
        verifier = PatchVerifier(self.test_dir, inspector, executor)
        
        engine = AutonomousEngine(
            repo_path=self.test_dir,
            git_inspector=inspector,
            lesson_parser=parser,
            hypothesis_generator=generator,
            patch_executor=executor,
            patch_verifier=verifier
        )

        unique_target_string = f"DATA_{uuid.uuid4().hex}"
        random_patch_data = {
            "file_path": self.random_file_name,
            "content": f"{self.random_content}\n# {unique_target_string}\n"
        }

        result = engine.run_autonomous_loop(random_patch_data)

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertTrue(result["success"], "Контур самообучения должен успешно верифицировать и применить патч.")

        verified_file_path = os.path.join(self.test_dir, self.random_file_name)
        self.assertTrue(os.path.exists(verified_file_path), "Файл должен существовать после работы движка.")

        with open(verified_file_path, "r", encoding="utf-8") as f:
            file_data = f.read()

        self.assertIn(unique_target_string, file_data, "Изменения от сгенерированной гипотезы/патча должны быть записаны в репозиторий.")

if __name__ == "__main__":
    unittest.main()