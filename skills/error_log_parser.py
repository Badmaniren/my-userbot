class ErrorLogParser:
    def __init__(self):
        self.known_categories = {
            "timeout": "Network/Timeout",
            "connection": "Network/Timeout",
            "nullpointerexception": "NullPointer",
            "critical": "Critical",
            "database": "Database"
        }

    def parse_log(self, filepath: str) -> str:
        with open(filepath, 'rb') as f:
            content = f.read()
        return content.decode('utf-8', errors='ignore')

    def safe_parse(self, filepath: str) -> str:
        try:
            return self.parse_log(filepath)
        except IOError:
            return ""

    def parse(self, raw_log: str) -> str:
        return raw_log

    def categorize(self, error_message: str) -> bool:
        if not error_message:
            return False
        lower_msg = error_message.lower()
        for keyword in self.known_categories:
            if keyword in lower_msg:
                return True
        return False