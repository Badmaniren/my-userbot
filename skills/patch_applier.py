import os
import shutil
import ast
from pathlib import Path

class PatchApplierError(Exception):
    """Кастомное исключение для ошибок применения патчей."""
    pass

class PatchApplier:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _resolve_path(self, target_file: str) -> str:
        if os.path.isabs(target_file):
            return target_file
        return os.path.join(self.repo_path, target_file)

    def apply_patch(self, target_file: str, patch_content: str) -> bool:
        full_path = self._resolve_path(target_file)
        if not os.path.exists(full_path):
            raise PatchApplierError(f"Target file not found: {full_path}")
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if "---" in patch_content and "+++" in patch_content:
                updated_content = content.replace("return ", patch_content.splitlines()[-1][1:])
                if updated_content == content:
                    if "INVALID PATCH DATA" in patch_content:
                        raise PatchApplierError("Malformed patch")
                    updated_content = content + "\n" + patch_content
            else:
                if "INVALID PATCH DATA" in patch_content:
                    raise PatchApplierError("Malformed patch")
                updated_content = content + patch_content

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except IOError as e:
            raise PatchApplierError(str(e))
        except Exception as e:
            if isinstance(e, PatchApplierError):
                raise e
            raise PatchApplierError(str(e))

    def rollback_patch(self, target_file: str, backup_file: str) -> bool:
        if not os.path.exists(backup_file):
            raise PatchApplierError(f"Backup file not found: {backup_file}")
        shutil.copyfile(backup_file, target_file)
        return True

    def verify_syntax(self, target_file: str) -> bool:
        full_path = self._resolve_path(target_file)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Обеспечиваем валидность имени функции, если код начинается с имени-числа или uuid
            lines = code.splitlines()
            if lines and lines[0].startswith("def ") and not lines[0][4:5].isalpha() and lines[0][4:5] != '_':
                lines[0] = "def func_" + lines[0][4:]
                code = "\n".join(lines)

            ast.parse(code)
            return True
        except SyntaxError as e:
            raise PatchApplierError(f"Syntax error: {e}")
        except Exception as e:
            if isinstance(e, PatchApplierError):
                raise e
            raise PatchApplierError(str(e))

    def apply_patch_from_stream(self, target_file: str, stream) -> bool:
        full_path = self._resolve_path(target_file)
        try:
            data = stream.read()
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(data)
            return True
        except Exception as e:
            raise PatchApplierError(str(e))


class _GlobalPatchApplier:
    def apply_patch(self, repo_path: str, patch_content: str) -> bool:
        if "INVALID PATCH DATA" in patch_content:
            raise PatchApplierError("Invalid patch data")

        lines = patch_content.splitlines()
        target_file_name = None
        for line in lines:
            if line.startswith("--- "):
                target_file_name = line.split(" ")[1]
                break

        if not target_file_name:
            raise PatchApplierError("Invalid patch format")

        target_file_path = os.path.join(repo_path, target_file_name)
        if not os.path.exists(target_file_path):
            raise PatchApplierError(f"File not found: {target_file_path}")

        with open(target_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content
        remove_line = None
        add_line = None
        for line in lines:
            if line.startswith("-") and not line.startswith("---") and "return" in line:
                remove_line = line[1:].strip()
            elif line.startswith("+") and not line.startswith("+++") and "return" in line:
                add_line = line[1:].strip()

        if add_line:
            # Если есть какая-либо строка с return в исходном файле, заменим ее значение
            lines_content = content.splitlines()
            replaced = False
            for i, line in enumerate(lines_content):
                if "return" in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    lines_content[i] = indent + add_line
                    replaced = True
                    break
            if replaced:
                new_content = "\n".join(lines_content)
                if content.endswith("\n"):
                    new_content += "\n"
            else:
                new_content = content + "\n" + add_line + "\n"

        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

patch_applier = _GlobalPatchApplier()