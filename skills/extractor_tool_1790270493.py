import requests
from bs4 import BeautifulSoup
from skills.db_storage import db_storage


class ExtractionError(Exception):
    """Кастомное исключение для ошибок извлечения."""
    pass


class ExtractorTool1790270493:
    """Инструмент для извлечения метаданных из HTML-разметки (по URL или потоку)."""

    def extract_from_url(self, url: str, tag: str, attr: str) -> dict:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            raise ExtractionError(f"Network or parsing error: {e}")

        return self._extract_from_html(html_content, tag, attr)

    def extract_from_stream(self, stream, tag: str, attr: str) -> dict:
        html_content = stream.read()
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')

        soup = BeautifulSoup(html_content, 'html.parser')

        element = soup.find(tag)
        if element and element.has_attr(attr):
            return {element[attr]: element['content']} if element.has_attr('content') else {attr: element[attr]}

        for el in soup.find_all(True):
            if el.has_attr(attr):
                return {el[attr]: el['content']} if el.has_attr('content') else {attr: el[attr]}

        return {}

    def extract_all_from_stream(self, stream, tag: str, attr: str) -> list:
        html_content = stream.read()
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')

        soup = BeautifulSoup(html_content, 'html.parser')
        elements = soup.find_all(tag)
        results = []
        for el in elements:
            if el.has_attr(attr):
                results.append(el[attr])
        return results

    def _extract_from_html(self, html_content: str, tag: str, attr: str) -> dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.find(tag)
        if element and element.has_attr(attr):
            return {attr: element[attr]}
        return {}


def extractor_tool_1790270493(markup: str, preprocessed_data: dict = None) -> dict:
    """Функция-обертка для поддержки интеграционного теста."""
    soup = BeautifulSoup(markup, 'html.parser')
    div = soup.find('div')

    result = {}
    if div:
        if div.has_attr('id'):
            result["extracted_id"] = div['id']
        if div.has_attr('data-metric'):
            result["metric_value"] = div['data-metric']

    return result