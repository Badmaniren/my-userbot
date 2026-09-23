import unittest
from unittest.mock import patch, MagicMock
import io
import random
import string
import uuid
import requests
from bs4 import BeautifulSoup
from skills.extractor_tool_1790171837 import MetadataExtractor

class TestMetadataExtractor(unittest.TestCase):
    def _generate_random_string(self, length=15):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_url(self):
        return f"https://{uuid.uuid4().hex}.{random.choice(['com', 'io', 'net'])}/{uuid.uuid4().hex}"

    def test_extract_standard_meta_tags_logic(self):
        """Проверка извлечения стандартных мета-тегов с рандомными именами."""
        extractor = MetadataExtractor()
        random_name_1 = f"name_{uuid.uuid4().hex[:8]}"
        random_content_1 = f"content_{uuid.uuid4().hex}"
        random_name_2 = f"author_{uuid.uuid4().hex[:8]}"
        random_content_2 = self._generate_random_string(20)

        html_content = f"""
        <html>
            <head>
                <meta name="{random_name_1}" content="{random_content_1}">
                <meta name="{random_name_2}" content="{random_content_2}">
                <title>{self._generate_random_string()}</title>
            </head>
            <body></body>
        </html>
        """

        result = extractor.extract(html_content)

        self.assertIn(random_name_1, result)
        self.assertEqual(result[random_name_1], random_content_1)
        self.assertIn(random_name_2, result)
        self.assertEqual(result[random_name_2], random_content_2)

    def test_extract_opengraph_tags_logic(self):
        """Проверка извлечения OpenGraph разметки с динамическими данными."""
        extractor = MetadataExtractor()
        og_title = f"Title_{uuid.uuid4().hex}"
        og_image = self._generate_random_url()
        og_type = random.choice(["article", "website", "video.movie"])

        html_content = f"""
        <html>
            <head>
                <meta property="og:title" content="{og_title}">
                <meta property="og:image" content="{og_image}">
                <meta property="og:type" content="{og_type}">
            </head>
        </html>
        """

        result = extractor.extract(html_content)

        self.assertEqual(result.get("og:title"), og_title)
        self.assertEqual(result.get("og:image"), og_image)
        self.assertEqual(result.get("og:type"), og_type)

    def test_extraction_from_binary_stream(self):
        """Проверка работы с потоками ввода (io.BytesIO) вместо строк."""
        extractor = MetadataExtractor()
        key = f"key_{uuid.uuid4().hex[:5]}"
        val = f"val_{uuid.uuid4().hex[:5]}"
        raw_html = f'<html><meta name="{key}" content="{val}"></html>'.encode('utf-8')

        binary_stream = io.BytesIO(raw_html)
        result = extractor.extract(binary_stream)

        self.assertEqual(result.get(key), val)

    def test_external_request_integration(self):
        """Проверка интеграции с внешними запросами через моки."""
        extractor = MetadataExtractor()
        target_url = self._generate_random_url()
        expected_key = f"ext_{uuid.uuid4().hex[:4]}"
        expected_val = f"data_{uuid.uuid4().hex[:10]}"

        mock_html = f'<html><meta name="{expected_key}" content="{expected_val}"></html>'

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.status_code = 200
            mock_response.content = mock_html.encode('utf-8')
            mock_get.return_value = mock_response

            # Предполагается, что у экстрактора есть метод для загрузки по URL
            # Если нет, тестируем через передачу текста из мока
            result = extractor.extract(requests.get(target_url).text)

            self.assertEqual(result.get(expected_key), expected_val)
            mock_get.assert_called_once_with(target_url)

    def test_empty_input_handling(self):
        """Проверка обработки пустых строк и некорректных типов."""
        extractor = MetadataExtractor()

        # Тест пустой строки
        self.assertEqual(extractor.extract(""), {})

        # Тест только пробелов
        self.assertEqual(extractor.extract("   \n\t   "), {})

        # Тест None (если архитектура подразумевает обработку)
        with self.assertRaises(Exception):
            extractor.extract(None)

    def test_complex_nested_markup(self):
        """Проверка извлечения при наличии сложной вложенности и мусора."""
        extractor = MetadataExtractor()
        secret_id = uuid.uuid4().hex
        noise = "".join(random.choices(string.printable, k=100))

        html = f"""
        <div>{noise}</div>
        <section>
            <aside>
                <meta name="deep_key" content="{secret_id}">
            </aside>
        </section>
        <span>{self._generate_random_string()}</span>
        """

        result = extractor.extract(html)
        self.assertEqual(result.get("deep_key"), secret_id)

    def test_duplicate_tags_behavior(self):
        """Проверка поведения при дублировании тегов (должен браться последний или список)."""
        extractor = MetadataExtractor()
        tag_name = "duplicate_test"
        val1 = "first_" + uuid.uuid4().hex
        val2 = "second_" + uuid.uuid4().hex

        html = f"""
        <meta name="{tag_name}" content="{val1}">
        <meta name="{tag_name}" content="{val2}">
        """

        result = extractor.extract(html)
        # Логика может зависеть от реализации, обычно берется последнее значение
        self.assertIn(result.get(tag_name), [val1, val2])

if __name__ == "__main__":
    unittest.main()