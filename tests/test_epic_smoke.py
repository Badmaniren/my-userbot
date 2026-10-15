import os
import shutil
import tempfile
import unittest

from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor
from skills.patch_verifier import PatchVerifier
from skills.autonomous_engine import AutonomousEngine


class TestAutonomousEngineEpicRealExecution(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ung_epic_test_")

        # Initialize a real Git repository in the temp directory
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Runner'")
        os.system(f"git -C {self.test_dir} config user.email 'test@ung.local'")

        # Create a realistic file that needs improvement / fixing (Anti-cheat simulation context)
        self.target_file = os.path.join(self.test_dir, "detector.py")
        initial_content = (
            "def check_memory():\n"
            "    # TODO: implement memory integrity check\n"
            "    pass\n"
        )
        with open(self.target_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        os.system(f"git -C {self.test_dir} add detector.py")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit with weak detector stub'")

        # Add a "lesson" commit that demonstrates how memory check should be implemented
        improved_content = (
            "def check_memory():\n"
            "    # Verified memory check implementation\n"
            "    return True\n"
        )
        with open(self.target_file, "w", encoding="utf-8") as f:
            f.write(improved_content)

        os.system(f"git -C {self.test_dir} add detector.py")
        os.system(f"git -C {self.test_dir} commit -m 'Lesson: implement robust memory integrity check returning True'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_autonomous_learning_loop_real_execution(self):
        print("\n=== НАЧАЛО РЕАЛЬНОЙ ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")

        # 1. Initialize GitInspector on the real repository
        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        print(f"[GitInspector] Найдено коммитов в репозитории: {len(history)}")
        for commit in history:
            print(f"  - [{commit.get('hash', 'N/A')[:7]}] {commit.get('message', '')}")
        self.assertGreaterEqual(len(history), 2, "Должно быть как минимум 2 коммита в истории")

        # 2. Parse lessons using LessonParser
        parser = LessonParser(inspector)
        lessons = parser.parse_lessons()
        print(f"[LessonParser] Извлечено уроков/паттернов: {len(lessons)}")

        # 3. Generate hypotheses via HypothesisGenerator
        generator = HypothesisGenerator(inspector, parser)
        hypotheses = generator.generate_hypotheses(max_commits=5)
        print(f"[HypothesisGenerator] Сгенерировано гипотез: {len(hypotheses)}")

        prioritized = generator.prioritize_hypotheses(hypotheses)
        print(f"[HypothesisGenerator] Приоритизированные гипотезы: {len(prioritized)}")

        # 4. Initialize Executor and Verifier
        executor = PatchExecutor(self.test_dir, inspector, parser)
        verifier = PatchVerifier(self.test_dir, inspector, executor)

        # 5. Run full AutonomousEngine cycle
        engine = AutonomousEngine(
            repo_path=self.test_dir,
            git_inspector=inspector,
            lesson_parser=parser,
            hypothesis_generator=generator,
            patch_executor=executor,
            patch_verifier=verifier
        )

        print("[AutonomousEngine] Запуск цикла анализа, верификации и исправления...")
        cycle_result = engine.run_cycle(max_commits=5)
        print(f"[AutonomousEngine] Результат выполнения run_cycle: {cycle_result}")

        # 6. Test direct verification and application of a synthesized patch payload
        sample_patch_data = {
            "file_path": "detector.py",
            "content": "def check_memory():\n    # Autonomous patch applied successfully\n    return True\n",
            "commit_hash": history[0].get("hash", "")
        }

        verification_result = verifier.verify_and_apply(sample_patch_data)
        print(f"[PatchVerifier] Статус верификации и применения патча: {verification_result}")
        self.assertTrue(verification_result, "Верификатор должен успешно подтвердить и применить валидный патч")

        # Read back the file to confirm changes were physically written to disk
        with open(self.target_file, "r", encoding="utf-8") as f:
            final_file_content = f.read()
        print(f"[ФИНАЛЬНОЕ СОСТОЯНИЕ ФАЙЛА detector.py]:\n{final_file_content}")

        self.assertIn("Autonomous patch applied successfully", final_file_content)
        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()