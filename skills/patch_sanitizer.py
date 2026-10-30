import io


class PatchSanitizerError(Exception):
    """Кастомное исключение для ошибок санитизации патчей."""
    pass


class PatchSanitizer:
    """Модуль первичной очистки и нормализации входящих патчей."""

    def _read_content(self, source) -> str:
        if isinstance(source, dict):
            return source.get("content", "")
        if isinstance(source, str):
            return source
        if isinstance(source, bytes):
            return source.decode("utf-8", errors="ignore")
        if hasattr(source, "read"):
            content = source.read()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore")
            return str(content)
        return str(source)

    def sanitize(self, stream) -> str:
        content = self._read_content(stream)
        if not content:
            raise PatchSanitizerError("Empty stream is not allowed.")
        if "\x00" in content:
            raise PatchSanitizerError("Null bytes detected in patch.")
        
        # Сначала убираем бинарные диффы, затем нормализуем окончания строк и убираем лишние пробелы
        cleaned_stream = io.StringIO(content)
        without_binary = self.remove_binary_diffs(cleaned_stream)
        
        normalized = self.normalize_endings(io.StringIO(without_binary))
        lines = normalized.splitlines()
        cleaned_lines = []
        for line in lines:
            cleaned_lines.append(line.rstrip())
        
        result = "\n".join(cleaned_lines)
        if result and not result.endswith("\n"):
            result += "\n"
        return result

    def normalize_endings(self, stream) -> str:
        content = self._read_content(stream)
        return content.replace("\r\n", "\n").replace("\r", "\n")

    def strip_whitespace(self, stream) -> str:
        content = self._read_content(stream)
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.rstrip() + ("\n" if normalized.endswith("\n") else "")

    def remove_binary_diffs(self, stream) -> str:
        content = self._read_content(stream)
        lines = content.splitlines()
        filtered_lines = []
        for line in lines:
            if "Binary files" in line and "differ" in line:
                continue
            filtered_lines.append(line)
        return "\n".join(filtered_lines)


def sanitize_patch(raw_patch: str) -> str:
    """Функция-обертка для интеграционных тестов."""
    sanitizer = PatchSanitizer()
    stream = io.StringIO(raw_patch)
    return sanitizer.sanitize(stream)