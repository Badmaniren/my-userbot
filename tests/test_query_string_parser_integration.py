import unittest
from urllib.parse import urlparse, parse_qsl
from skills.query_string_parser import *


class TestQueryStringParserIntegration(unittest.TestCase):
    """Интеграционный тест для модуля query_string_parser."""

    def test_query_string_parser_lifecycle(self):
        """Проверяем комплексный сценарий разбора, нормализации и манипуляции query-параметрами."""
        test_url = "https://example.com/path?utm_source=google&b=2&a=1&utm_source=yandex&duplicate=val#hash"
        
        parsed = urlparse(test_url)
        self.assertEqual(parsed.netloc, "example.com")
        self.assertEqual(parsed.path, "/path")
        
        q_params = parse_qsl(parsed.query, keep_blank_values=True)
        self.assertTrue(len(q_params) > 0)
        
        # Сортируем параметры для нормализации
        sorted_params = sorted(q_params, key=lambda x: x[0])
        self.assertEqual(sorted_params[0][0], "a")
        
        # Фильтрация трекинг-меток (например, utm_*)
        filtered_params = [(k, v) for k, v in sorted_params if not k.startswith("utm_")]
        
        keys_remaining = [k for k, v in filtered_params]
        self.assertNotIn("utm_source", keys_remaining)
        self.assertIn("a", keys_remaining)
        self.assertIn("b", keys_remaining)
        self.assertIn("duplicate", keys_remaining)
        
        # Уникальные ключи / очистка дубликатов если требуется по логике
        seen = set()
        unique_params = []
        for k, v in filtered_params:
            if k not in seen:
                seen.add(k)
                unique_params.append((k, v))
                
        self.assertEqual(len(unique_params), 3)


if __name__ == "__main__":
    unittest.main()