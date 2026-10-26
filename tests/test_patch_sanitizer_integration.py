import unittest
import uuid
import random
from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError, sanitize_patch


class TestPatchSanitizerIntegration(unittest.TestCase):

    def test_patch_sanitizer_integration_flow(self):
        random_id = str(uuid.uuid4())
        trailing_spaces_patch = f"diff --git a/file.py b/file.py   \n+print('{random_id}')    \r\n-old_line   \r"
        
        sanitizer = PatchSanitizer()
        
        # Интеграционная проверка через публичный метод с потоком
        stream_result = sanitizer.sanitize(sanitize_patch.__globals__['io'].StringIO(trailing_spaces_patch))
        
        # Проверка отсутствия \r и правых пробелов, сохранение содержимого со случайным ID
        self.assertNotIn("\r", stream_result)
        self.assertIn(f"+print('{random_id}')", stream_result)
        
        for line in stream_result.splitlines():
            self.assertEqual(line, line.rstrip())

        # Интеграционная проверка функции-обертки
        wrapper_result = sanitize_patch(trailing_spaces_patch)
        self.assertEqual(stream_result, wrapper_result)

        # Проверка удаления бинарных дифов
        binary_patch = f"Binary files a/bin_{random_id} and b/bin_{random_id} differ\nIndex: file.py\n+content_{random_id}"
        cleaned_binary = sanitizer.remove_binary_diffs(sanitize_patch.__globals__['io'].StringIO(binary_patch))
        self.assertNotIn("Binary files", cleaned_binary)
        self.assertIn(f"+content_{random_id}", cleaned_binary)

        # Проверка исключения при пустом потоке
        with self.assertRaises(PatchSanitizerError):
            sanitizer.sanitize(sanitize_patch.__globals__['io'].StringIO(""))

        # Проверка исключения при наличии нулевых байтов
        with self.assertRaises(PatchSanitizerError):
            sanitizer.sanitize(sanitize_patch.__globals__['io'].StringIO(f"test\x00{random_id}"))


if __name__ == "__main__":
    unittest.main()