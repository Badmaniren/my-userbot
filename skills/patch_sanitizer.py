import io


class PatchSanitizerError(Exception):
    """Кастомное исключение для ошибок санитизации патчей."""
    pass


class PatchSanitizer:
    """Модуль первичной очистки и нормализации входящих патчей."""

    def _to_stream(self, stream):
        if isinstance(stream, str):
            return io.StringIO(stream)
        if isinstance(stream, bytes):
            return io.StringIO(stream.decode("utf-8", errors="ignore"))
        if hasattr(stream, "read"):
            return stream
        return io.StringIO(str(stream))

    def sanitize(self, stream) -> str:
        stream_obj = self._to_stream(stream)
        content = stream_obj.read()
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
        stream_obj = self._to_stream(stream)
        content = stream_obj.read()
        return content.replace("\r\n", "\n").replace("\r", "\n")

    def strip_whitespace(self, stream) -> str:
        stream_obj = self._to_stream(stream)
        content = stream_obj.read()
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.rstrip() + ("\n" if normalized.endswith("\n") else "")

    def remove_binary_diffs(self, stream) -> str:
        stream_obj = self._to_stream(stream)
        content = stream_obj.read()
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