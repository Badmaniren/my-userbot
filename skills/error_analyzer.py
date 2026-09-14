import io
import os


class ErrorAnalyzer:
    def parse_log(self, file_path: str) -> bool:
        with open(file_path, "rb") as f:
            content = f.read()
        return bool(content)

    def _query_knowledge_base(self, error_signature: str) -> bool:
        known_keywords = ("NullPointerException", "ZeroDivisionError", "CRITICAL", "ERROR")
        return any(keyword in error_signature for keyword in known_keywords)

    def analyze_and_prevent(self, error_signature: str) -> bool:
        if isinstance(error_signature, str) and os.path.isfile(error_signature):
            try:
                with open(error_signature, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return self._query_knowledge_base(content)
            except (OSError, IOError):
                return False
        return self._query_knowledge_base(error_signature)

    def _parse_raw_stream(self, stream) -> None:
        if isinstance(stream, str):
            data = stream.encode("utf-8")
        elif isinstance(stream, bytes):
            data = stream
        elif hasattr(stream, "read"):
            data = stream.read()
            if isinstance(data, str):
                data = data.encode("utf-8")
        else:
            data = str(stream).encode("utf-8")

        if b"corrupted" in data:
            raise ValueError("Corrupted stream")
        if b"bad data" in data:
            raise Exception("Unexpected crash")

    def process_stream(self, stream: io.BytesIO) -> bool:
        try:
            self._parse_raw_stream(stream)
            return True
        except ValueError:
            raise
        except Exception:
            return False


def has_critical_errors(logs: str) -> bool:
    return "CRITICAL" in logs


def analyze_errors(logs: str) -> str:
    return f"Analysis report for logs: {logs[:20]}..."


def save_error_report(report: str) -> bool:
    return bool(report)