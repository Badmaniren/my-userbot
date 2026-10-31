import unittest
import tempfile
import os
from patch_sanitizer import patch_sanitizer
from patch_analyzer import patch_analyzer
from patch_checker import patch_checker
from patch_evaluator import patch_evaluator
from patch_verifier import patch_verifier
from patch_applier import patch_applier

class TestPatchPipelineEpicPractical(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.target_file = os.path.join(self.test_dir.name, "target_code.py")
        
        # Создаем исходный файл для применения патча
        with open(self.target_file, "w", encoding="utf-8") as f:
            f.write("def calculate_sum(a, b):\n    return a + b\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_safe_patch_pipeline_end_to_end(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Безопасный пайплайн исправления патчей ===")
        
        # Сырой патч с лишними пробелами и потенциально опасными конструкциями
        raw_patch = """
        --- target_code.py
        +++ target_code.py
        @@ -1,2 +1,2 @@
         def calculate_sum(a, b):
        -    return a + b
        +    return a + b # Fixed implementation with comment
        """
        print(f"[1] Сырой патч создан (длина: {len(raw_patch)} символов).")

        # Шаг 1: Санитизация (patch_sanitizer)
        sanitized_patch = patch_sanitizer.sanitize(raw_patch)
        print(f"[2] Шаг санитизации (patch_sanitizer) выполнен успешно. Нормализованный патч:\n{sanitized_patch}")

        # Шаг 2: Анализ структуры патча (patch_analyzer)
        analysis_result = patch_analyzer.analyze(sanitized_patch)
        print(f"[3] Шаг анализа (patch_analyzer) завершен. Результат структуры: {analysis_result}")
        self.assertIsNotNone(analysis_result)

        # Шаг 3: Проверка патча (patch_checker)
        check_result = patch_checker.check(sanitized_patch, self.target_file)
        print(f"[4] Шаг проверки (patch_checker) завершен. Статус проверки: {check_result}")

        # Шаг 4: Оценка патча (patch_evaluator)
        evaluation_result = patch_evaluator.evaluate(sanitized_patch)
        print(f"[5] Шаг оценки (patch_evaluator) завершен. Оценка безопасности/качества: {evaluation_result}")

        # Шаг 5: Финальная верификация (patch_verifier)
        verification_passed = patch_verifier.verify(sanitized_patch, self.target_file)
        print(f"[6] Шаг верификации (patch_verifier) пройден: {verification_passed}")
        self.assertTrue(verification_passed)

        # Шаг 6: Применение патча (patch_applier)
        apply_success = patch_applier.apply(sanitized_patch, self.target_file)
        print(f"[7] Шаг применения (patch_applier) завершен. Успех: {apply_success}")
        self.assertTrue(apply_success)

        # Проверяем реальное содержимое файла после применения патча
        with open(self.target_file, "r", encoding="utf-8") as f:
            updated_content = f.read()
        print(f"[8] Итоговое содержимое файла на диске после пайплайна:\n{updated_content}")
        
        self.assertIn("Fixed implementation", updated_content)
        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    unittest.main()