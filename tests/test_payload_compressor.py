import base64
import json
import unittest
from unittest.mock import patch
import zlib

from skills.payload_compressor import (
    PayloadCompressor,
    PayloadCompressorError,
    CompressionError,
    DecompressionError,
    compress_text,
    decompress_text,
    compress_json,
    decompress_json,
)


class TestPayloadCompressor(unittest.TestCase):
    """Агрессивный набор тестов для модуля skills.payload_compressor."""

    def test_exception_hierarchy(self):
        """Проверка корректной иерархии исключений."""
        self.assertTrue(issubclass(PayloadCompressorError, Exception))
        self.assertTrue(issubclass(CompressionError, PayloadCompressorError))
        self.assertTrue(issubclass(DecompressionError, PayloadCompressorError))

    # ==================== УСПЕШНЫЕ СЦЕНАРИИ ====================

    def test_compress_and_decompress_simple_text(self):
        """Проверка сжатия и декомпрессии базовой строки."""
        payload = "Hello, World! Minimal free tier compression test."
        compressed = compress_text(payload)
        self.assertIsInstance(compressed, str)
        decompressed = decompress_text(compressed)
        self.assertEqual(decompressed, payload)

    def test_compress_and_decompress_empty_text(self):
        """Проверка сжатия пустой строки."""
        compressed = compress_text("")
        self.assertIsInstance(compressed, str)
        decompressed = decompress_text(compressed)
        self.assertEqual(decompressed, "")

    def test_compress_and_decompress_large_text(self):
        """Проверка сжатия повторяющегося текста и эффективности сжатия."""
        repeated_data = "Free-tier RAM and storage optimization benchmark. " * 500
        compressed = compress_text(repeated_data)
        decompressed = decompress_text(compressed)
        self.assertEqual(decompressed, repeated_data)
        self.assertLess(len(compressed), len(repeated_data))

    def test_compress_and_decompress_multilingual_unicode(self):
        """Проверка корректной обработки Unicode символов (кириллица, emoji, CJK)."""
        unicode_payload = "Привет мир! 🚀 123 中文 текст with symbols: \n\t\r\\//'\""
        compressed = compress_text(unicode_payload)
        decompressed = decompress_text(compressed)
        self.assertEqual(decompressed, unicode_payload)

    def test_compress_and_decompress_json_dict(self):
        """Проверка сжатия и восстановления сложного JSON-словаря."""
        data = {
            "user_id": 42,
            "username": "tester",
            "active": True,
            "quota_left": 0.005,
            "metadata": None,
            "roles": ["admin", "editor"],
            "nested": {"score": 99.9, "flags": [False, True]},
        }
        compressed = compress_json(data)
        self.assertIsInstance(compressed, str)
        restored = decompress_json(compressed)
        self.assertEqual(restored, data)

    def test_compress_and_decompress_json_list(self):
        """Проверка сжатия и восстановления JSON-списка."""
        data = [{"id": i, "val": f"item_{i}"} for i in range(50)]
        compressed = compress_json(data)
        restored = decompress_json(compressed)
        self.assertEqual(restored, data)

    def test_payload_compressor_class_instance(self):
        """Проверка работы через экземпляр класса PayloadCompressor."""
        compressor = PayloadCompressor(default_level=9)
        text = "Class instance test string"
        compressed = compressor.compress_text(text)
        self.assertEqual(compressor.decompress_text(compressed), text)

        json_obj = {"tier": "free", "mem_limit_mb": 512}
        comp_json = compressor.compress_json(json_obj)
        self.assertEqual(compressor.decompress_json(comp_json), json_obj)

    def test_compression_levels(self):
        """Проверка сжатия с разными уровнями (1 и 9)."""
        payload = "Compressible text stream for compression level validation. " * 300
        comp_level_1 = compress_text(payload, level=1)
        comp_level_9 = compress_text(payload, level=9)
        self.assertEqual(decompress_text(comp_level_1), payload)
        self.assertEqual(decompress_text(comp_level_9), payload)
        self.assertLessEqual(len(comp_level_9), len(comp_level_1))

    # ==================== СБОИ, КРАЕВЫЕ СЛУЧАИ, НЕВАЛИДНЫЕ ДАННЫЕ (>50%) ====================

    def test_compress_text_invalid_type_none(self):
        """Сбой: передача None в compress_text должна вызывать CompressionError."""
        with self.assertRaises(CompressionError):
            compress_text(None)

    def test_compress_text_invalid_type_int(self):
        """Сбой: передача целого числа в compress_text должна вызывать CompressionError."""
        with self.assertRaises(CompressionError):
            compress_text(123456)

    def test_compress_text_invalid_type_bytes(self):
        """Сбой: передача bytes вместо str в compress_text должна вызывать CompressionError."""
        with self.assertRaises(CompressionError):
            compress_text(b"raw binary data")

    def test_compress_text_invalid_level_overflow(self):
        """Сбой: некорректный уровень сжатия (> 9) должен вызывать CompressionError."""
        with self.assertRaises(CompressionError):
            compress_text("valid text", level=99)

    def test_compress_text_invalid_level_negative(self):
        """Сбой: отрицательный уровень сжатия (вне диапазона zlib) вызывает CompressionError."""
        with self.assertRaises(CompressionError):
            compress_text("valid text", level=-5)

    def test_compress_text_invalid_level_type(self):
        """Сбой: нечисловой уровень сжатия вызывает CompressionError."""
        with self.assertRaises(CompressionError):
            compress_text("valid text", level="maximum")

    def test_decompress_text_invalid_type_none(self):
        """Сбой: передача None в decompress_text должна вызывать DecompressionError."""
        with self.assertRaises(DecompressionError):
            decompress_text(None)

    def test_decompress_text_invalid_type_bytes(self):
        """Сбой: передача bytes в decompress_text должна вызывать DecompressionError."""
        with self.assertRaises(DecompressionError):
            decompress_text(b"invalid bytes")

    def test_decompress_text_corrupted_base64(self):
        """Сбой: некорректный base64 вызывает DecompressionError."""
        with self.assertRaises(DecompressionError):
            decompress_text("ThisIsNotValidBase64!!!@@@###$$$")

    def test_decompress_text_valid_base64_invalid_zlib(self):
        """Сбой: валидный base64, но байты не являются zlib-контейнером."""
        fake_payload = base64.b64encode(b"plain non-zlib raw bytes").decode("ascii")
        with self.assertRaises(DecompressionError):
            decompress_text(fake_payload)

    def test_decompress_text_truncated_payload(self):
        """Сбой: обрезанный сжатый payload должен вызывать DecompressionError."""
        valid_compressed = compress_text("Important mission data to be truncated")
        truncated = valid_compressed[: len(valid_compressed) // 2]
        with self.assertRaises(DecompressionError):
            decompress_text(truncated)

    def test_decompress_text_invalid_utf8_payload(self):
        """Сбой: валидный zlib сжатый байтовый поток с невалидным UTF-8 вызывает DecompressionError."""
        invalid_utf8_bytes = b"\xff\xfe\xfd\x80\x81\x82"
        compressed_bad_bytes = base64.b64encode(zlib.compress(invalid_utf8_bytes)).decode("ascii")
        with self.assertRaises(DecompressionError):
            decompress_text(compressed_bad_bytes)

    def test_compress_json_unserializable_object(self):
        """Сбой: сериализация произвольного объекта вызывает CompressionError."""
        class CustomNonSerializable:
            pass

        with self.assertRaises(CompressionError):
            compress_json(CustomNonSerializable())

    def test_compress_json_unserializable_set(self):
        """Сбой: тип set не поддерживается стандартным JSON сериализатором."""
        with self.assertRaises(CompressionError):
            compress_json({"numbers": {1, 2, 3}})

    def test_compress_json_unserializable_lambda(self):
        """Сбой: функция/лямбда вызывает CompressionError."""
        with self.assertRaises(CompressionError):
            compress_json(lambda x: x * 2)

    def test_decompress_json_invalid_type(self):
        """Сбой: передача невалидного типа в decompress_json вызывает DecompressionError."""
        with self.assertRaises(DecompressionError):
            decompress_json(None)

    def test_decompress_json_corrupted_base64(self):
        """Сбой: битый base64 в decompress_json вызывает DecompressionError."""
        with self.assertRaises(DecompressionError):
            decompress_json("not-base64---string")

    def test_decompress_json_valid_text_not_json(self):
        """Сбой: распакованные данные не являются валидным JSON (вызывает DecompressionError)."""
        compressed_plain_string = compress_text("This is just regular text, not JSON at all!")
        with self.assertRaises(DecompressionError):
            decompress_json(compressed_plain_string)

    def test_payload_compressor_init_invalid_level(self):
        """Сбой: создание PayloadCompressor с невалидным уровнем сжатия вызывает CompressionError."""
        with self.assertRaises(CompressionError):
            PayloadCompressor(default_level=999)

    def test_mocked_zlib_compress_failure(self):
        """Сбой: ошибка zlib при сжатии перехватывается и оборачивается в CompressionError."""
        with patch("skills.payload_compressor.zlib.compress", side_effect=zlib.error("Mocked zlib engine crash")):
            with self.assertRaises(CompressionError):
                compress_text("Some text that should fail")


if __name__ == "__main__":
    unittest.main()