import os
import sys
import tempfile
import inspect
import unittest

import patch_analyzer
import patch_evaluator
import patch_checker
import patch_verifier
import patch_reporter


class TestSafeAutoCorrectionPipeline(unittest.TestCase):
    """
    Практическая проверка сквозного конвейера безопасного автоисправления:
    Анализатор (patch_analyzer) -> Оценщик (patch_evaluator) ->
    Проверяющий (patch_checker) -> Верификатор (patch_verifier) -> Репортер (patch_reporter).
    """

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.patch_path = os.path.join(cls.temp_dir.name, "fix_zero_division.patch")

        # Реалистичный унифицированный diff (26 строк) с исправлением ошибки деления на ноль
        cls.realistic_patch_content = (
            "--- a/services/billing/calculator.py\n"
            "+++ b/services/billing/calculator.py\n"
            "@@ -15,10 +15,18 @@ class BillingCalculator:\n"
            "     def calculate_rate(self, total_sum: float, count: int) -> float:\n"
            "         # Вычисление среднего коэффициента биллинга\n"
            "-        return total_sum / count\n"
            "+        if count <= 0:\n"
            "+            logger.warning('Invalid count value %s; returning default 0.0', count)\n"
            "+            return 0.0\n"
            "+        result = total_sum / count\n"
            "+        return round(result, 4)\n"
            " \n"
            "     def process_transactions(self, transactions: list) -> list:\n"
            "         results = []\n"
            "         for tx in transactions:\n"
            "-            val = self.calculate_rate(tx.amount, tx.qty)\n"
            "-            results.append(val)\n"
            "+            rate = self.calculate_rate(tx.amount, tx.qty)\n"
            "+            results.append({'id': tx.id, 'rate': rate})\n"
            "         return results\n"
        )

        with open(cls.patch_path, "w", encoding="utf-8") as f:
            f.write(cls.realistic_patch_content)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    @staticmethod
    def _find_and_execute(module, class_name, method_candidates, *args, **kwargs):
        """
        Универсальный диспетчер для вызова методов компонентов конвейера,
        поддерживающий инстанцирование классов или прямые вызовы функций модуля.
        """
        target_cls = getattr(module, class_name, None)
        runner = None

        if target_cls and isinstance(target_cls, type):
            try:
                runner = target_cls()
            except Exception:
                try:
                    runner = target_cls(*args)
                    args = ()
                except Exception:
                    runner = target_cls
        elif target_cls and callable(target_cls):
            runner = target_cls

        if runner is not None:
            for method_name in method_candidates:
                method = getattr(runner, method_name, None)
                if callable(method):
                    sig = inspect.signature(method)
                    valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                    return method(*args, **valid_kwargs)
            if callable(runner):
                sig = inspect.signature(runner)
                valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                return runner(*args, **valid_kwargs)

        for method_name in method_candidates:
            fn = getattr(module, method_name, None)
            if callable(fn):
                sig = inspect.signature(fn)
                valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                return fn(*args, **valid_kwargs)

        raise AttributeError(
            f"Не удалось найти подходящий исполнитель в {module.__name__} для {class_name} "
            f"с методами {method_candidates}"
        )

    def test_end_to_end_pipeline(self):
        print("\n" + "=" * 70)
        print(">>> ЗАПУСК СКВОЗНОЙ ПРОВЕРКИ КОНВЕЙЕРА БЕЗОПАСНОГО АВТОИСПРАВЛЕНИЯ")
        print("=" * 70)

        # 1. Чтение патча с диска
        with open(self.patch_path, "r", encoding="utf-8") as f:
            patch_text = f.read()
        self.assertTrue(len(patch_text) > 0, "Патч не должен быть пустым")
        print(f"[1] Прочитан файл патча: {self.patch_path} ({len(patch_text.splitlines())} строк)")

        # 2. Звено 1: patch_analyzer (Анализатор)
        analysis_result = self._find_and_execute(
            patch_analyzer,
            "PatchAnalyzer",
            ["analyze", "analyze_patch", "parse_patch", "parse", "process"],
            patch_text=patch_text,
            patch=patch_text,
            diff_text=patch_text
        )
        self.assertIsNotNone(analysis_result, "Результат PatchAnalyzer не должен быть пустым")
        print("\n[2] Результаты анализатора (patch_analyzer):")
        print(f"    Тип: {type(analysis_result)}")
        print(f"    Данные анализа: {analysis_result}")

        # 3. Звено 2: patch_evaluator (Оценщик)
        evaluation_result = self._find_and_execute(
            patch_evaluator,
            "PatchEvaluator",
            ["evaluate", "evaluate_patch", "assess_risks", "evaluate_risk", "calculate_risk"],
            analysis=analysis_result,
            analysis_result=analysis_result,
            patch_analysis=analysis_result,
            patch=patch_text,
            patch_text=patch_text
        )
        self.assertIsNotNone(evaluation_result, "Результат PatchEvaluator не должен быть пустым")
        print("\n[3] Результаты оценщика рисков (patch_evaluator):")
        print(f"    Тип: {type(evaluation_result)}")
        print(f"    Оценка: {evaluation_result}")

        # 4. Звено 3: patch_checker (Проверяющий / Предварительный вердикт)
        checker_verdict = self._find_and_execute(
            patch_checker,
            "PatchChecker",
            ["check", "check_patch", "verify_safety", "pre_check", "execute_check"],
            analysis=analysis_result,
            evaluation=evaluation_result,
            patch_analysis=analysis_result,
            patch_evaluation=evaluation_result,
            patch=patch_text,
            patch_text=patch_text
        )
        self.assertIsNotNone(checker_verdict, "Результат PatchChecker не должен быть пустым")
        print("\n[4] Результаты предварительной проверки (patch_checker):")
        print(f"    Тип: {type(checker_verdict)}")
        print(f"    Вердикт: {checker_verdict}")

        # 5. Звено 4: patch_verifier (Верификатор)
        verification_result = self._find_and_execute(
            patch_verifier,
            "PatchVerifier",
            ["verify", "verify_patch", "run_verification", "validate_patch", "check"],
            checker_verdict=checker_verdict,
            verdict=checker_verdict,
            analysis=analysis_result,
            evaluation=evaluation_result,
            patch_text=patch_text,
            patch=patch_text
        )
        self.assertIsNotNone(verification_result, "Результат PatchVerifier не должен быть пустым")
        print("\n[5] Результаты верификации (patch_verifier):")
        print(f"    Тип: {type(verification_result)}")
        print(f"    Верификация: {verification_result}")

        # 6. Звено 5: patch_reporter (Репортер - агрегация в единый отчет)
        final_report = self._find_and_execute(
            patch_reporter,
            "PatchReporter",
            ["generate_report", "create_report", "build_report", "report", "aggregate"],
            analysis=analysis_result,
            analysis_result=analysis_result,
            evaluation=evaluation_result,
            evaluation_result=evaluation_result,
            checker_verdict=checker_verdict,
            verification=verification_result,
            verification_result=verification_result,
            patch_text=patch_text
        )
        self.assertIsNotNone(final_report, "Итоговый отчет PatchReporter не должен быть пустым")

        print("\n[6] Итоговый отчет конвейера (patch_reporter):")
        print("-" * 50)
        if isinstance(final_report, (dict, list)):
            import json
            print(json.dumps(final_report, indent=2, ensure_ascii=False, default=str))
        else:
            print(final_report)
        print("-" * 50)
        print(">>> ПРОВЕРКА КОНВЕЙЕРА УСПЕШНО ЗАВЕРШЕНА: все звенья обработали реальный diff.\n")


if __name__ == "__main__":
    unittest.main()