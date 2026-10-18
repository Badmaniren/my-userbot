import json
import os
from typing import Any, Dict, Optional, Union


class AuditSerializer:
    def __init__(self, data: Optional[Any] = None):
        self.data = data if data is not None else {}

    def to_json(self, data: Optional[Any] = None) -> str:
        target_data = self.data if data is None else data
        return json.dumps(target_data, indent=2)

    def serialize_json(self, data: Optional[Any] = None) -> str:
        target_data = self.data if data is None else data
        return json.dumps(target_data, indent=2)

    def _dict_to_markdown(self, data: Any, indent_level: int = 0) -> str:
        lines = []
        indent = "  " * indent_level
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, (dict, list)):
                    lines.append(f"{indent}- **{key}**:")
                    sub = self._dict_to_markdown(val, indent_level + 1)
                    if sub:
                        lines.append(sub)
                else:
                    lines.append(f"{indent}- **{key}**: {val}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}-")
                    sub = self._dict_to_markdown(item, indent_level + 1)
                    if sub:
                        lines.append(sub)
                else:
                    lines.append(f"{indent}- {item}")
        else:
            lines.append(f"{indent}{data}")
        return "\n".join(lines)

    def to_markdown(self, data: Optional[Any] = None) -> str:
        return self.serialize_markdown(data)

    def serialize_markdown(self, data: Optional[Any] = None) -> str:
        target_data = self.data if data is None else data
        if not target_data and target_data != 0 and target_data is not False:
            return "# Audit Report\n\nEmpty report."
        lines = ["# Audit Report\n"]
        body = self._dict_to_markdown(target_data)
        if body:
            lines.append(body)
        return "\n".join(lines)

    def save(self, filepath: str, format: str = "json", data: Optional[Any] = None) -> str:
        fmt = format.lower()
        if fmt == "json":
            content = self.to_json(data)
        elif fmt in ("md", "markdown"):
            content = self.to_markdown(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def save_json(self, arg1: Any, arg2: Optional[str] = None) -> str:
        if arg2 is None:
            data = self.data
            filepath = arg1
        else:
            data = arg1
            filepath = arg2

        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        content = self.serialize_json(data)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def save_markdown(self, arg1: Any, arg2: Optional[str] = None) -> str:
        if arg2 is None:
            data = self.data
            filepath = arg1
        else:
            data = arg1
            filepath = arg2

        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        content = self.serialize_markdown(data)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath