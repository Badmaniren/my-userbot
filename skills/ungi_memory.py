import json
import os

LESSON_FILE_PATH = "ungi_lesson.json"

class UngiMemory:
    def __init__(self, filepath: str = None):
        self.filepath = filepath or LESSON_FILE_PATH

    def read(self, strict: bool = False) -> any:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
        except (IOError, OSError) as e:
            if strict:
                raise e
            return False

    def write(self, data: any) -> bool:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, ensure_ascii=False)
                else:
                    f.write(str(data))
            return True
        except (IOError, OSError, PermissionError, TypeError):
            return False

    def validate(self, data: any) -> bool:
        return isinstance(data, dict)

def read_ungi_lesson() -> str:
    path = globals().get("LESSON_FILE_PATH", "ungi_lesson.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (IOError, OSError):
        return ""

def write_ungi_lesson(content: str) -> bool:
    path = globals().get("LESSON_FILE_PATH", "ungi_lesson.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
        return True
    except (IOError, OSError, PermissionError):
        return False