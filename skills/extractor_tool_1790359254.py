import requests
import bs4
import json
import os

class MetadataExtractor:
    def extract(self, url):
        response = requests.get(url)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')

        result = {}
        target = soup.find(lambda tag: getattr(tag, 'has_attr', lambda a: False)('id'))
        if target:
            result['id'] = target.get('id')
            for attr, value in target.attrs.items():
                if attr.startswith('data-'):
                    result[attr.replace('data-', '', 1)] = value
        return result

    def process_stream(self, stream):
        if hasattr(stream, 'read'):
            stream = stream.read()
        soup = bs4.BeautifulSoup(stream, 'html.parser')
        element = soup.find()
        if not element:
            return None
        return self._map_elements(soup)

    def _map_elements(self, soup):
        mapping = {}
        elements = soup.find_all(True)
        for el in elements:
            if hasattr(el, 'attrs'):
                mapping.update(el.attrs)
        return mapping

def extract_metadata(file_path):
    """
    Функция-обертка для интеграционного теста.
    Предполагается, что файл содержит JSON-структуру,
    которую нужно извлечь как метаданные.
    """
    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}
