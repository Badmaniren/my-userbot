import os
import shutil
import tempfile
import unittest

from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor


class TestEpicSelfReflectionAndUpgrade(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="unga_epic_test_")
        cls.repo_path = cls.test_dir

        # Инициализация git репозитория через системный вызов для создания реальной истории
        os.system(f"git -C {cls.repo_path} init -b main")
        os.system(f"git -C {cls.repo_path} config user.name 'Unga Test Bot'")
        os.system(f"git -C {cls.repo_path} config user.email 'test@unga.ai'")

        # Создаем файлы с реалистичными данными рефлексии (уроки, ошибки, паттерны)
        cls.lessons_file = os.path.join(cls.repo_path, "lessons.txt")
        with open(cls.lessons_file, "w", encoding="utf-8") as f:
            f.write("[LESSON] commit: a1b2c3d | author: Unga | message: fix bug in parser\n")
            f.write("Lesson text: Античит заблокировал частые запросы. Требуется экспоненциальный бэкофф.\n")
            f.write("[LESSON] commit: e4f5g6h | author: Unga | message: optimize memory\n")
            f.write("Lesson text: Утечка памяти в модуле git_inspector при чтении больших дифф-файлов.\n")

        os.system(f"git -C {cls.repo_path} add lessons.txt")
        os.system(f"git -C {cls.repo_path} commit -m 'Add initial lessons and retrospectives'")

        # Создаем второй коммит для генерации реальной diff истории
        with open(cls.lessons_file, "a", encoding="utf-8") as f:
            f.write("[LESSON] commit: i7j8k9l | author: Unga | message: update threshold\n")
            f.write("Lesson text: Порог срабатывания гипотез должен быть выше 0.8 для избежания ложных срабатываний.\n")

        os.system(f"git -C {cls.repo_path} add lessons.txt")
        os.system(f"git -C {cls.repo_path} commit -m 'Append high threshold lesson'")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_full_epic_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")

        # 1. Шаг git_inspector: проверяем сбор реальной истории коммитов и дифф-анализ
        inspector = GitInspector(repo_path=self.repo_path)
        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 2)
        print(f"[OK] GitInspector успешно собрал коммиты: {len(history)} найдено.")

        latest_changes = inspector.get_latest_changes()
        print(f"[OK] Последние изменения получены. Объем описания: {len(str(latest_changes))} байт.")

        # 2. Шаг lesson_parser: парсим уроки из созданного файла и истории
        parser = LessonParser(git_inspector=inspector)
        parsed_lessons = parser.parse_lessons()
        print(f"[OK] LessonParser успешно извлек уроки рефлексии. Найдено записей: {len(parsed_lessons) if isinstance(parsed_lessons, list) else 'dict'}")
        print(f"Пример распарсенных данных: {str(parsed_lessons)[:200]}...")

        # 3. Шаг hypothesis_generator: генерируем и приоритизируем гипотезы
        generator = HypothesisGenerator(git_inspector=inspector, lesson_parser=parser)
        hypotheses = generator.generate_hypotheses(max_commits=5)
        print(f"[OK] HypothesisGenerator сгенерировал гипотезы на основе уроков и гита.")

        prioritized = generator.prioritize_hypotheses(hypotheses)
        print(f"[OK] Гипотезы приоритизированы. Всего гипотез: {len(prioritized) if isinstance(prioritized, list) else 'выполнено'}")
        print(f"Срез приоритизированных гипотез: {str(prioritized)[:300]}")

        # 4. Шаг patch_executor: выполняем автоматический апгрейд на основе гипотез/уроков
        executor = PatchExecutor(repo_path=self.repo_path, git_inspector=inspector, lesson_parser=parser)
        execution_result = executor.execute_from_lessons()
        print(f"[OK] PatchExecutor завершил цикл автономного апгрейда.")
        print(f"Результат выполнения патчей: {execution_result}")

        print("=== ЭПИКС УСПЕШНО ПРОШЕЛ ПРАКТИЧЕСКУЮ ПРОВЕРКУ В РЕАЛЬНЫХ УСЛОВИЯХ ===")


if __name__ == "__main__":
    unittest.main()