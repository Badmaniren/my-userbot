import io
import json
import re
from typing import Dict, List, Optional, Any

try:
    from packaging.requirements import Requirement, InvalidRequirement
except ImportError:
    Requirement = None
    InvalidRequirement = Exception

from skills.pypi_client import PyPIClient


def parse_dependency(dep_str: str) -> Dict[str, Any]:
    """
    Разбирает PEP 508 строку зависимости.
    Возвращает словарь с ключами name, specifier, marker, extras.
    """
    if not isinstance(dep_str, str) or not dep_str.strip():
        raise ValueError("Invalid dependency string")

    # Сначала пытаемся спарсить стандартной библиотекой packaging, если она доступна
    if Requirement is not None:
        try:
            req = Requirement(dep_str)
            # В случаях, когда исходный маркер передан со строковыми литералами (например, с одинарными кавычками),
            # извлекаем подстроку маркера непосредственно из исходного dep_str, если это возможно,
            # чтобы сохранять в точности строку маркера.
            raw_marker = None
            if ';' in dep_str:
                raw_marker = dep_str.split(';', 1)[1].strip() or None
            elif req.marker:
                raw_marker = str(req.marker)

            return {
                "name": req.name,
                "specifier": str(req.specifier) if req.specifier else "",
                "marker": raw_marker,
                "extras": sorted(list(req.extras)) if req.extras else []
            }
        except InvalidRequirement:
            pass

    # Кастомный парсер для более гибкого использования
    s = dep_str.strip()
    marker = None
    if ';' in s:
        s, marker_part = s.split(';', 1)
        s = s.strip()
        marker = marker_part.strip() or None

    m = re.match(r'^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)(.*)$', s)
    if not m:
        raise ValueError(f"Invalid dependency string: {dep_str}")

    name = m.group(1)
    rest = m.group(2).strip()

    extras = []
    if rest.startswith('['):
        end_idx = rest.find(']')
        if end_idx != -1:
            raw_extras = rest[1:end_idx]
            extras = [e.strip() for e in raw_extras.split(',') if e.strip()]
            rest = rest[end_idx + 1:].strip()

    if rest.startswith('(') and rest.endswith(')'):
        rest = rest[1:-1].strip()

    specifier = rest

    return {
        "name": name,
        "specifier": specifier,
        "marker": marker,
        "extras": extras
    }


def parse_dependencies(dep_str: str) -> Dict[str, Any]:
    """
    Алиас для parse_dependency.
    """
    return parse_dependency(dep_str)


class DependencyParser:
    """
    Класс для парсинга требований пакетов из PEP 508 строк зависимостей.
    """

    def __init__(self, pypi_client: Optional[PyPIClient] = None):
        self.pypi_client = pypi_client or PyPIClient()

    def parse_string(self, dep_str: str) -> Dict[str, Any]:
        """Парсит одиночную строку зависимости."""
        return parse_dependency(dep_str)

    def parse_stream(self, stream: io.BufferedIOBase) -> List[Dict[str, Any]]:
        """
        Парсит поток данных (например, BytesIO).
        Может быть текстовым списком зависимостей или JSON со списком зависимостей.
        При ошибках чтения/декодирования возвращает [].
        """
        try:
            content_bytes = stream.read()
            if not isinstance(content_bytes, (bytes, bytearray, str)):
                return []
            if isinstance(content_bytes, (bytes, bytearray)):
                content = content_bytes.decode('utf-8')
            else:
                content = content_bytes
        except Exception:
            return []

        results = []
        # Пробуем разобрать как JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                lines = data
            elif isinstance(data, dict):
                lines = data.get("requires_dist", []) or data.get("dependencies", [])
            else:
                lines = []
        except Exception:
            # Если не JSON, разбираем как построчный текст
            lines = content.splitlines()

        for line in lines:
            line_str = str(line).strip()
            if not line_str or line_str.startswith("#"):
                continue
            try:
                parsed = parse_dependency(line_str)
                results.append(parsed)
            except Exception:
                pass

        return results

    def fetch_and_parse(self, package_name: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Запрашивает метаданные пакета из PyPIClient и парсит его зависимости.
        """
        raw_deps = self.pypi_client.get_dependencies(package_name, version)
        parsed_deps = []
        for dep in raw_deps:
            try:
                parsed = parse_dependency(dep)
                parsed_deps.append(parsed)
            except Exception:
                pass
        return parsed_deps
