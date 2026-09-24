import unittest
import random
import uuid
import skills.extractor_tool_1790257535 as extractor_module

class TestExtractorToolIntegration(unittest.TestCase):
    def test_extraction_flow_with_random_markup(self):
        # Генерируем случайные данные для исключения хардкода
        unique_suffix = str(uuid.uuid4())[:8]
        expected_title = f"Target_Title_{unique_suffix}"
        expected_author = f"Author_{random.randint(1000, 9999)}"
        expected_description = f"Description_Content_{unique_suffix}"

        # Формируем разметку со случайными метаданными
        markup = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{expected_title}</title>
            <meta name="author" content="{expected_author}">
            <meta name="description" content="{expected_description}">
            <meta property="og:type" content="article">
        </head>
        <body>
            <h1>Main Content</h1>
        </body>
        </html>
        """

        # Динамически определяем точку входа в тестируемом модуле
        if hasattr(extractor_module, "ExtractorTool"):
            extractor = extractor_module.ExtractorTool()
            result = extractor.extract(markup)
        elif hasattr(extractor_module, "extract_metadata"):
            result = extractor_module.extract_metadata(markup)
        elif hasattr(extractor_module, "extract"):
            result = extractor_module.extract(markup)
        else:
            raise AttributeError("Не найден метод извлечения в модуле skills/extractor_tool_1790257535.py")

        # Проверяем корректность интеграции и извлечения реальных данных
        self.assertIsNotNone(result, "Результат извлечения не должен быть None")
        self.assertIsInstance(result, dict, "Результат должен быть словарем")

        # Проверяем соответствие извлеченных данных сгенерированным случайным значениям
        self.assertEqual(result.get("title"), expected_title, "Заголовок не совпадает с ожидаемым")
        self.assertEqual(result.get("author"), expected_author, "Автор не совпадает с ожидаемым")
        self.assertEqual(result.get("description"), expected_description, "Описание не совпадает с ожидаемым")
        self.assertEqual(result.get("og:type"), "article", "Тип og:type не совпадает с ожидаемым")

if __name__ == "__main__":
    unittest.main()