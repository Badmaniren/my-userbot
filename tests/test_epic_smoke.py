import unittest
import tempfile
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from patch_analyzer import patch_analyzer
from patch_evaluator import patch_evaluator
from patch_checker import patch_checker
from patch_verifier import patch_verifier
from patch_reporter import patch_reporter


class TestSafeAutocorrectionPipelineLive(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.patch_file_path = os.path.join(self.test_dir.name, "sample_fix.patch")
        
        sample_diff = (
            "diff --git a/app/core.py b/app/core.py\n"
            "index 83db4fc..2f864fa 100644\n"
            "--- a/app/core.py\n"
            "+++ b/app/core.py\n"
            "@@ -10,7 +10,7 @@ def process_data(payload):\n"
            "     if not payload:\n"
            "-        raise ValueError('Empty payload')\n"
            "+        return None\n"
            " \n"
            "     result = []\n"
            "     for item in payload:\n"
            "         result.append(item * 2)\n"
            "     return result\n"
        )
        
        with open(self.patch_file_path, "w", encoding="utf-8") as f:
            f.write(sample_diff)
            
    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_execution_live(self):
        print("\n[LIVE CHECK] Запуск практической проверки конвейера безопасного автоисправления...")
        
        with open(self.patch_file_path, "r", encoding="utf-8") as f:
            patch_content = f.read()
            
        print(f"[LIVE CHECK] Загружен реальный патч из файла: {self.patch_file_path}")
        print(f"Содержимое патча:\n{patch_content}")

        analysis_result = patch_analyzer.analyze(patch_content)
        print(f"[LIVE CHECK] Шаг 1 (Analyzer) выполнен. Структура анализа: {analysis_result}")
        self.assertIsNotNone(analysis_result)

        evaluation_result = patch_evaluator.evaluate(analysis_result)
        print(f"[LIVE CHECK] Шаг 2 (Evaluator) выполнен. Оценка рисков: {evaluation_result}")
        self.assertIsNotNone(evaluation_result)

        check_result = patch_checker.check(analysis_result, evaluation_result)
        print(f"[LIVE CHECK] Шаг 3 (Checker) выполнен. Предварительный вердикт: {check_result}")
        self.assertIsNotNone(check_result)

        verification_result = patch_verifier.verify(check_result, patch_content)
        print(f"[LIVE CHECK] Шаг 4 (Verifier) выполнен. Результат верификации: {verification_result}")
        self.assertIsNotNone(verification_result)

        final_report = patch_reporter.generate_report(
            analysis=analysis_result,
            evaluation=evaluation_result,
            check=check_result,
            verification=verification_result
        )
        print(f"[LIVE CHECK] Шаг 5 (Reporter) финализировал конвейер. Итоговый отчет:\n{json.dumps(final_report, indent=2, ensure_ascii=False)}")
        self.assertIsNotNone(final_report)
        print("[LIVE CHECK] Эпик успешно прошел проверку на реальных данных!")


if __name__ == "__main__":
    unittest.main()