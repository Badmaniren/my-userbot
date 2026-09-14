import os

MEMORY_FILE_PATH = "lessons.txt"

class UngiMemory:
    def __init__(self, file_path="lessons.txt"):
        self.file_path = file_path

    def read_memory(self) -> str:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def write_memory(self, data: str) -> bool:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(data)
            return True
        except PermissionError:
            return False

    def update_memory(self, data: str) -> bool:
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(data)
            return True
        except OSError:
            return False

    def strict_read_memory(self) -> str:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()


def read_ungi_memory() -> str:
    path = globals().get("MEMORY_FILE_PATH", "lessons.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def write_ungi_memory(data: str) -> bool:
    path = globals().get("MEMORY_FILE_PATH", "lessons.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        return True
    except OSError:
        return False


def update_ungi_memory(data: str) -> bool:
    path = globals().get("MEMORY_FILE_PATH", "lessons.txt")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(data)
        return True
    except OSError:
        return False