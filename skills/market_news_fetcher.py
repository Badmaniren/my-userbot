import re
from typing import List, Dict, Any, Union
import requests
from bs4 import BeautifulSoup

def extract_tickers(text: str) -> List[str]:
    """
    Извлекает финансовые тикеры из текста.
    Поддерживает форматы: $TICKER, EXCHANGE:TICKER, а также составные тикеры (например, TCK123),
    а также обычные заглавные слова (3-5 букв), если они похожи на тикеры.
    """
    if not text:
        return []

    tickers = set()

    # 1. Шаблон для совпадений вида $AAPL, NASDAQ:AAPL или TCK123 (буквы + цифры)
    pattern_explicit = r'(?:\$([A-Z0-9]{3,8})|(?:[A-Z]+:)?([A-Z0-9]{3,8}))'
    matches = re.findall(pattern_explicit, text)
    for match in matches:
        for t in match:
            if t:
                tickers.add(t)

    # 2. Ищем также слова с буквами и цифрами (например, TCK123)
    words = text.split()
    for word in words:
        clean_word = word.strip(".,!?()[]{}\"'").replace("$", "")
        # Если слово содержит от 3 до 8 символов, состоит из заглавных букв и/или цифр
        if any(c.isdigit() for c in clean_word) and clean_word.isalnum() and clean_word.isupper() and 3 <= len(clean_word) <= 8:
            tickers.add(clean_word)
            continue

        # Обычные чисто буквенные тикеры
        if clean_word.isupper() and 3 <= len(clean_word) <= 5 and clean_word.isalpha():
            if clean_word not in {"THE", "AND", "FOR", "BUT", "Q3", "Q1", "Q2", "Q4"}:
                tickers.add(clean_word)

    return list(tickers)


class MarketNewsFetcher:
    def __init__(self):
        self.storage = []

    def extract_tickers(self, text: str) -> List[str]:
        return extract_tickers(text)

    def fetch_html(self, url: str) -> str:
        """Загружает HTML-страницу по URL."""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def fetch_news(self, raw_content: str, source: str = "default_source") -> List[Dict[str, Any]]:
        """Парсит новости из HTML или XML сырого контента."""
        parsed_items = []
        
        content = raw_content
        if raw_content.startswith("http://") or raw_content.startswith("https://"):
            content = self.fetch_html(raw_content)

        if not content:
            return parsed_items

        soup = BeautifulSoup(content, 'html.parser')

        # Ищем статьи (<article> или <item>)
        articles = soup.find_all(['article', 'item'])
        if not articles:
            title_tag = soup.find(['h1', 'h2', 'title'])
            title_text = title_tag.get_text() if title_tag else content[:100]
            parsed_items.append({
                "title": title_text,
                "tickers": extract_tickers(content),
                "source": source
            })
            return parsed_items

        for art in articles:
            title_elem = art.find(['h1', 'h2', 'h3', 'title'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            body_elem = art.find(['p', 'description', 'content'])
            body = body_elem.get_text(strip=True) if body_elem else art.get_text(strip=True)

            item_id = art.get('id') or art.find('guid')
            if hasattr(item_id, 'get_text'):
                item_id = item_id.get_text(strip=True)

            combined_text = f"{title} {body}"
            tickers = extract_tickers(combined_text)

            item = {
                "id": item_id,
                "title": title or combined_text[:80],
                "body": body,
                "tickers": tickers,
                "source": source
            }
            parsed_items.append(item)

        return parsed_items

    def save_to_storage(self, items: List[Dict[str, Any]]) -> int:
        """Сохраняет элементы новостей в локальное хранилище."""
        count = 0
        for item in items:
            self.storage.append(item)
            count += 1
        return count

    def get_stored_news(self, source: str = None) -> List[Dict[str, Any]]:
        """Возвращает сохраненные новости, опционально фильтруя по источнику."""
        if source:
            return [item for item in self.storage if item.get("source") == source]
        return self.storage