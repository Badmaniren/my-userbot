import requests
import json

class PyPIClient:
    """Клиент для работы с PyPI JSON API."""

    def __init__(self, base_url: str = "https://pypi.org/pypi"):
        self.base_url = base_url

    def get_package_metadata(self, package_name: str, version: str = None) -> dict:
        """Получает метаданные пакета из PyPI."""
        url = f"{self.base_url}/{package_name}/json" if not version else f"{self.base_url}/{package_name}/{version}/json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_release_versions(self, package_name: str) -> list:
        """Возвращает список доступных версий релизов пакета."""
        data = self.get_package_metadata(package_name)
        if data and "releases" in data:
            return list(data["releases"].keys())
        return []

    def get_dependencies(self, package_name: str, version: str = None) -> list:
        """Возвращает список объявленных зависимостей (requires_dist) для указанного пакета/версии."""
        data = self.get_package_metadata(package_name, version)
        if data and "info" in data:
            requires_dist = data["info"].get("requires_dist")
            if requires_dist:
                return requires_dist
        return []

    def get_package_dependencies(self, package_name: str, version: str = None) -> list:
        """Алиас или дополнительный метод для получения зависимостей, совместимый с интеграционным тестом."""
        data = self.get_package_metadata(package_name, version)
        if data is None:
            raise ValueError(f"Package {package_name} (version {version}) not found on PyPI")
        if "info" in data:
            requires_dist = data["info"].get("requires_dist")
            if requires_dist:
                return requires_dist
        return []

    def parse_stream_data(self, stream) -> dict:
        """Парсит JSON из потока (например, BytesIO), возвращает None при поврежденных данных."""
        try:
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            return json.loads(content)
        except Exception:
            return None