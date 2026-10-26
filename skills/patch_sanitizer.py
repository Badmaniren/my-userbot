import io


class PatchSanitizerError(Exception):
    """Кастомное исключение для ошибок санитизации патчей."""
    pass


class PatchSanitizer:
    """Модуль первичной очистки и нормализации входящих патчей."""

    def sanitize(self, stream):
        if isinstance(stream, dict):
            res = dict(stream)
            for key in ("content", "payload"):
                if key in res and isinstance(res[key], str):
                    res[key] = self.sanitize(res[key])
            return res
        if isinstance(stream, bytes):
            stream = stream.decode("utf-8")
        if isinstance(stream, str):
            stream = io.StringIO(stream)

        content = stream.read()
        if not content:
            raise PatchSanitizerError("Empty stream is not allowed.")
        if "\x00" in content:
            raise PatchSanitizerError("Null bytes detected in patch.")
        
        # Нормализация окончаний строк и удаление лишних пробелов на концах строк
        normalized = self.normalize_endings(io.StringIO(content))
        lines = normalized.splitlines()
        cleaned_lines = []
        for line in lines:
            # Убираем пробелы справа, сохраняя перенос
            cleaned_lines.append(line.rstrip())
        
        return "\n".join(cleaned_lines)

    def normalize_endings(self, stream) -> str:
        content = stream.read()
        return content.replace("\r\n", "\n").replace("\r", "\n")

    def strip_whitespace(self, stream) -> str:
        content = stream.read()
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.rstrip() + ("\n" if normalized.endswith("\n") else "")

    def remove_binary_diffs(self, stream) -> str:
        content = stream.read()
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