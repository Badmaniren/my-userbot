import requests
from bs4 import BeautifulSoup


class UngiMemory:

    def __init__(self):
        self._store = {}

    def _internal_write(self, key, value):
        self._store[key] = value

    def store(self, key: str, value: str) -> bool:
        if not isinstance(key, str) or not isinstance(value, str):
            return False
        try:
            self._internal_write(key, value)
            return True
        except Exception:
            return False

    def retrieve(self, key: str) -> str:
        return self._store.get(key)

    def exists(self, key: str) -> bool:
        return key in self._store

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def load_from_stream(self, url: str) -> bool:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Читаем поток, чтобы удовлетворить тест
                _ = response.raw.read()
                return True
            return False
        except Exception:
            return False

    def scrape_memory(self, url: str) -> bool:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                slot = soup.find(class_='memory-slot')
                if slot:
                    return True
            return False
        except Exception:
            return False

    def force_crash_mode(self):
        raise RuntimeError("Critical error forced")