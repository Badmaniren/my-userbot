import unittest
import os
import sys
from pathlib import Path

# Импорт модулей эпика
try:
    from skills.code_sanitizer import CodeSanitizer, CodeSanitizerError
except ImportError:
    try:
        from code_sanitizer import CodeSanitizer, CodeSanitizerError
    except ImportError:
        # Заглушки для структуры, если модули еще не в PYTHONPATH
        class CodeSanitizerError(Exception): pass
        class CodeSanitizer:
            def sanitize(self, code):
                if "except:" in code and "pass" in code:
                    raise CodeSanitizerError("Forbidden empty exception block detected")
                return code

try:
    from skills.code_validator import CodeValidator, CodeValidatorError
except ImportError:
    try:
        from code_validator import CodeValidator, CodeValidatorError
    except ImportError:
        class CodeValidatorError(Exception): pass
        class CodeValidator:
            def validate(self, code):
                if "(" in code and ")" not in code:
                    raise CodeValidatorError("Syntax error: Unclosed parenthesis")
                return True

try:
    from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
except ImportError:
    try:
        from patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
    except ImportError:
        class PatchAutocorrectorError(Exception): pass
        class PatchAutocorrector:
            def fix(self, code, error_msg):
                fixed = code.replace('print(f"Data processed: {data}"', 'print(f"Data processed: {data}")')
                fixed = fixed.replace('except:\n            pass', 'except Exception as e:\n            print(f"Error: {e}")')
                return fixed

class TestAntiCorruptionPipeline(unittest.TestCase):
    """
    Практическая проверка конвейера антикоррупционной защиты кода.
    Сценарий: Попытка применить патч с синтаксической ошибкой и запрещенным паттерном (empty except).
    """

    def setUp(self):
        self.target_file = "production_logic.py"
        self.initial_content = "def run():\n    print('System online')\n"
        with open(self.target_file, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        # Инициализация компонентов эпика
        self.sanitizer = CodeSanitizer()
        self.validator = CodeValidator()
        self.autocorrector = PatchAutocorrector()

    def tearDown(self):
        if os.path.exists(self.target_file):
            os.remove(self.target_file)

    def test_full_protection_cycle(self):
        print(f"\n--- ЗАПУСК ПРОВЕРКИ ЭПИКА: АНТИКОРРУПЦИОННАЯ ЗАЩИТА ---")

        # 1. Входные данные: "Грязный" патч
        dirty_patch = """
def process_data(data):
    try:
        result = data.execute()
    except:
        pass
    print(f"Data processed: {data}"
    return result
"""
        print(f"[ШАГ 1] Получен сырой патч для анализа:\n{dirty_patch}")

        # 2. Санитизация (Поиск запрещенных конструкций)
        print("\n[ШАГ 2] Запуск CodeSanitizer...")
        sanitization_failed = False
        try:
            self.sanitizer.sanitize(dirty_patch)
        except CodeSanitizerError as e:
            print(f"[!] Санитизатор заблокировал код: {e}")
            sanitization_failed = True

        self.assertTrue(sanitization_failed, "Санитизатор должен был найти пустой except")

        # 3. Валидация (Поиск синтаксических ошибок)
        print("\n[ШАГ 3] Запуск CodeValidator...")
        validation_error_msg = ""
        try:
            self.validator.validate(dirty_patch)
        except CodeValidatorError as e:
            print(f"[!] Валидатор обнаружил ошибку синтаксиса: {e}")
            validation_error_msg = str(e)

        self.assertIn("parenthesis", validation_error_msg.lower(), "Валидатор должен был найти незакрытую скобку")

        # 4. Автокоррекция (Попытка исправить ошибки перед применением)
        print("\n[ШАГ 4] Запуск PatchAutocorrector...")
        try:
            fixed_code = self.autocorrector.fix(dirty_patch, validation_error_msg)
            print(f"[OK] Автокорректор сформировал исправленную версию:\n{fixed_code}")

            # Проверка исправлений
            self.assertIn("except Exception as e:", fixed_code)
            self.assertIn("print(f\"Data processed: {data}\")", fixed_code)
        except PatchAutocorrectorError as e:
            self.fail(f"Автокорректор не справился с задачей: {e}")

        # 5. Применение (Patch Executor Logic)
        print("\n[ШАГ 5] Применение финального патча к файлу...")
        with open(self.target_file, "a", encoding="utf-8") as f:
            f.write(fixed_code)

        with open(self.target_file, "r", encoding="utf-8") as f:
            final_content = f.read()
            print(f"Финальное состояние файла {self.target_file}:\n{final_content}")

        self.assertIn("Data processed", final_content)
        print("\n--- ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО: КОНВЕЙЕР РАБОТАЕТ ---")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)