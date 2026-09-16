import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup

# Импорт тестируемого модуля
from skills.extractor_tool_1789544538 import MarkupMetadataExtractor, ExtractionError

class TestMarkupMetadataExtractor(unittest.TestCase):

    def test_extract_from_string_success(self):
        extractor = MarkupMetadataExtractor()
        
        # Генерация абсолютно случайных данных для предотвращения хардкода
        random_title = f"title_{uuid.uuid4().hex}"
        random_meta_name = f"meta_{uuid.uuid4().hex}"
        random_meta_value = f"val_{uuid.uuid4().hex}"
        random_og_property = f"og:{uuid.uuid4().hex}"
        random_og_value = f"og_val_{uuid.uuid4().hex}"
        random_body_content = f"body_{uuid.uuid4().hex}"

        html_markup = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{random_title}</title>
            <meta name="{random_meta_name}" content="{random_meta_value}">
            <meta property="{random_og_property}" content="{random_og_value}">
        </head>
        <body>
            <p>{random_body_content}</p>
        </body>
        </html>
        """

        result = extractor.extract_from_string(html_markup)

        # Смысловые проверки извлеченных метаданных
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("title"), random_title)
        self.assertEqual(result.get(random_meta_name), random_meta_value)
        self.assertEqual(result.get(random_og_property), random_og_value)

    def test_extract_from_file_success(self):
        extractor = MarkupMetadataExtractor()
        
        random_file_path = f"/path/to/dir_{uuid.uuid4().hex}/{uuid.uuid4().hex}.html"
        random_title = f"title_{uuid.uuid4().hex}"
        random_meta_name = f"meta_{uuid.uuid4().hex}"
        random_meta_value = f"val_{uuid.uuid4().hex}"

        html_markup = f"""
        <html>
        <head>
            <title>{random_title}</title>
            <meta name="{random_meta_name}" content="{random_meta_value}">
        </head>
        </html>
        """
        
        # Использование io.BytesIO для имитации бинарного потока чтения файла
        binary_data = html_markup.encode("utf-8")
        mock_file_stream = io.BytesIO(binary_data)

        with patch("builtins.open", return_value=mock_file_stream) as mock_file_open:
            result = extractor.extract_from_file(random_file_path)
            mock_file_open.assert_called_once_with(random_file_path, "rb")

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("title"), random_title)
        self.assertEqual(result.get(random_meta_name), random_meta_value)

    def test_extract_from_url_success(self):
        extractor = MarkupMetadataExtractor()
        
        random_domain = f"{uuid.uuid4().hex}.com"
        random_path = f"page_{uuid.uuid4().hex}"
        random_url = f"https://{random_domain}/{random_path}"
        
        random_title = f"title_{uuid.uuid4().hex}"
        random_meta_name = f"meta_{uuid.uuid4().hex}"
        random_meta_value = f"val_{uuid.uuid4().hex}"

        html_markup = f"""
        <html>
        <head>
            <title>{random_title}</title>
            <meta name="{random_meta_name}" content="{random_meta_value}">
        </head>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = html_markup.encode("utf-8")
            mock_get.return_value = mock_response

            result = extractor.extract_from_url(random_url)
            mock_get.assert_called_once_with(random_url, timeout=10)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("title"), random_title)
        self.assertEqual(result.get(random_meta_name), random_meta_value)

    def test_extract_from_url_http_error(self):
        extractor = MarkupMetadataExtractor()
        
        random_url = f"https://{uuid.uuid4().hex}.org/{uuid.uuid4().hex}"
        random_error_msg = f"Connection refused {uuid.uuid4().hex}"

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(random_error_msg)

            with self.assertRaises(ExtractionError) as context:
                extractor.extract_from_url(random_url)
            
            self.assertIn(random_error_msg, str(context.exception))

    def test_extract_from_corrupted_markup(self):
        extractor = MarkupMetadataExtractor()
        
        # Генерация случайного мусора вместо валидной разметки
        garbage_length = random.randint(50, 150)
        garbage_markup = "".join(random.choices(string.ascii_letters + string.digits + "<>/=", k=garbage_length))

        result = extractor.extract_from_string(garbage_markup)
        
        # Парсер не должен падать, а должен вернуть пустой или частично заполненный словарь без ключевых метаданных
        self.assertIsInstance(result, dict)
        self.assertNotIn("title", result)

    def test_extract_empty_markup(self):
        extractor = MarkupMetadataExtractor()
        
        result = extractor.extract_from_string("")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

if __name__ == "__main__":
    unittest.main()