import unittest
from unittest.mock import patch, MagicMock
import json

from skills.json_extractor import extract_json, JsonExtractorError


class TestJsonExtractorInquisitor(unittest.TestCase):
    """
    Архитектор-Инквизитор требует абсолютной стабильности от легковесного парсера JSON.
    Никаких внешних зависимостей. Только чистая логика, устойчивая к хаосу.
    """

    def setUp(self):
        self.valid_simple = '{"key": "value", "number": 42, "flag": true, "nothing": null}'
        self.valid_nested = '{"user": {"id": 1, "roles": ["admin", "user"]}, "active": false}'

    def test_extract_valid_simple_json(self):
        result = extract_json(self.valid_simple)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 42)
        self.assertTrue(result["flag"])
        self.assertIsNone(result["nothing"])

    def test_extract_valid_nested_json(self):
        result = extract_json(self.valid_nested)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["user"]["id"], 1)
        self.assertEqual(result["user"]["roles"], ["admin", "user"])
        self.assertFalse(result["active"])

    def test_extract_json_with_surrounding_garbage(self):
        """Инквизиция проверяет способность вычленить JSON из текстового мусора."""
        raw_text = 'Логи системы: some debug info before {"target": "found", "code": 200} и хвост мусора.'
        result = extract_json(raw_text)
        self.assertEqual(result.get("target"), "found")
        self.assertEqual(result.get("code"), 200)

    def test_fail_empty_string(self):
        """СБОЙ: Передан пустой текст."""
        with self.assertRaises((ValueError, JsonExtractorError)):
            extract_json("")

    def test_fail_whitespace_only(self):
        """СБОЙ: Переданы только пробелы и символы переноса строки."""
        with self.assertRaises((ValueError, JsonExtractorError)):
            extract_json("   \n\t   ")

    def test_fail_none_input(self):
        """СБОЙ: Передан тип None вместо строки."""
        with self.assertRaises((TypeError, JsonExtractorError)):
            extract_json(None)

    def test_fail_malformed_json_syntax(self):
        """СБОЙ: Поврежденный синтаксис JSON (незакрытая кавычка/скобка)."""
        broken_payloads = [
            '{"key": "value"',
            '{"key": unquoted}',
            '{"key": "value",}',
            '[1, 2, 3'
        ]
        for payload in broken_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises((ValueError, JsonExtractorError, json.JSONDecodeError)):
                    extract_json(payload)

    def test_fail_no_json_found_in_text(self):
        """СБОЙ: Текст не содержит никаких признаков JSON-структуры."""
        plain_text = "Это просто строка без единой фигурной или квадратной скобки."
        with self.assertRaises((ValueError, JsonExtractorError)):
            extract_json(plain_text)

    def test_fail_deeply_nested_malicious_payload(self):
        """СБОЙ: Слишком глубокая или сломанная вложенность."""
        deep_evil = '{"a": ' * 50 + '1' + '}' * 40 # Несоответствие скобок
        with self.assertRaises((ValueError, JsonExtractorError)):
            extract_json(deep_evil)

    def test_extract_json_array_root(self):
        """Проверка корректной обработки массива в качестве корневого элемента."""
        array_payload = '[{"id": 1}, {"id": 2}]'
        result = extract_json(array_payload)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)


if __name__ == "__main__":
    unittest.main()