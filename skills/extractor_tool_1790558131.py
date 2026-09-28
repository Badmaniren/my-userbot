import requests
from bs4 import BeautifulSoup
import os
import json
from skills.market_parser import MarketParser

def extract_metadata(source, from_file=False):
    """
    Извлекает метаданные из HTML-разметки.
    Поддерживает передачу URL (по умолчанию) или пути к файлу (если from_file=True).
    """
    try:
        if from_file:
            with open(source, 'rb') as f:
                content = f.read()
        else:
            response = requests.get(source, timeout=10)
            content = response.content

        soup = BeautifulSoup(content, 'html.parser')
        metadata = {}

        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content_val = meta.get('content')
            if name and content_val:
                metadata[name] = content_val

        return metadata
    except Exception as e:
        return {'error': str(e)}

def extractor_tool_1790558131(data):
    """
    Интеграционный инструмент для извлечения данных, совместимый с market_parser.
    """
    if isinstance(data, dict):
        return data

    soup = BeautifulSoup(str(data), 'html.parser')
    result = {}

    # Ищем элементы с id или текстом для интеграционного теста
    for tag in soup.find_all(True):
        if tag.get('id'):
            result[tag.get('id')] = tag.text

    if not result and soup.text:
        result['content'] = soup.text

    return result