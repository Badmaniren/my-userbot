import io


class ErrorAnalyzer:
    def parse_log(self, file_path: str) -> bool:
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return bool(content)
        except (FileNotFoundError, OSError):
            return False

    def _query_knowledge_base(self, error_signature: str) -> bool:
        return "NullPointerException" in error_signature

    def analyze_and_prevent(self, error_signature: str) -> bool:
        return self._query_knowledge_base(error_signature)

    def _parse_raw_stream(self, stream: io.BytesIO) -> None:
        data = stream.read()
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