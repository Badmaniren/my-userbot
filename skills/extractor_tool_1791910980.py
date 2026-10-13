import re

class MetadataExtractor:
    """
    Класс для извлечения метаданных из текстовой разметки.
    Поддерживает форматы [key: value] и <meta name="key" content="value">.
    """

    def __init__(self):
        # Регулярное выражение для формата [ключ: значение]
        self.bracket_pattern = re.compile(r'\[(?P<key>[a-zA-Z0-9._-]+):\s*(?P<value>[^\]]+)\]')
        
        # Регулярное выражение для HTML-подобных мета-тегов
        self.meta_pattern = re.compile(
            r'<meta\s+[^>]*name=["\'](?P<key>[^"\']+)["\']\s+[^>]*content=["\'](?P<value>[^"\']+)["\'][^>]*>'
        )

    def extract(self, text: str) -> dict:
        """
        Извлекает все найденные метаданные в словарь.
        Если входные данные не являются строкой, возвращает пустой словарь.
        """
        if not isinstance(text, str):
            return {}

        metadata = {}

        # Извлечение из формата [key: value]
        for match in self.bracket_pattern.finditer(text):
            key = match.group('key').strip()
            value = match.group('value').strip()
            metadata[key] = value

        # Извлечение из формата <meta name="..." content="...">
        for match in self.meta_pattern.finditer(text):
            key = match.group('key').strip()
            value = match.group('value').strip()
            metadata[key] = value

        return metadata

def extract_metadata(text: str) -> dict:
    """
    Удобная функция-обертка для быстрого извлечения метаданных.
    """
    extractor = MetadataExtractor()
    return extractor.extract(text)