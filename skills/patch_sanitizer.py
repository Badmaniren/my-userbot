import io


class PatchSanitizerError(Exception):
    """Кастомное исключение для ошибок санитизации патчей."""
    pass


class PatchSanitizer:
    """Модуль первичной очистки и нормализации входящих патчей."""

    def sanitize(self, stream) -> str:
        if isinstance(stream, str):
            stream = io.StringIO(stream)
        elif isinstance(stream, bytes):
            stream = io.BytesIO(stream)

        content = stream.read()
        if isinstance(content, bytes):
            if b"\x00" in content:
                raise PatchSanitizerError("Null bytes detected in patch.")
            content = content.decode("utf-8", errors="ignore")

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
        
        return "\n".join(cleaned_lines)

    def normalize_endings(self, stream) -> str:
        content = stream.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
        return content.replace("\r\n", "\n").replace("\r", "\n")

    def strip_whitespace(self, stream) -> str:
        content = stream.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.rstrip() + ("\n" if normalized.endswith("\n") else "")

    def remove_binary_diffs(self, stream) -> str:
        content = stream.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="ignore")
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