import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.patch_verifier import (
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier
)

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "ArchitectTest"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True)
        
        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_end_to_end_patch_verification_flow(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Random payload: {uuid.uuid4()}\nx = {random.randint(1, 1000)}"
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": commit_msg
        }

        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)

        hypotheses = self.generator.generate_hypotheses()
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertIsInstance(prioritized, list)

        success = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "Верификатор должен успешно одобрить и применить валидный патч")

        full_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(full_path), "Файл патча должен реально появиться в репозитории")

        with open(full_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content, "Содержимое файла должно совпадать с переданным в патче")

        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 1, "История коммитов должна содержать зафиксированный патч")
        self.assertEqual(history[0]["message"], commit_msg, "Сообщение последнего коммита должно соответствовать патчу")

        bad_patch_data = {
            "file_path": f"bad_{uuid.uuid4().hex[:8]}.py",
            "content": "syntax error here: invalid syntax !!!",
            "commit_message": "Should fail"
        }
        fail_success = self.verifier.verify_and_apply(bad_patch_data)
        self.assertFalse(fail_success, "Верификатор должен отклонить патч с признаками синтаксической ошибки")

if __name__ == "__main__":
    unittest.main()