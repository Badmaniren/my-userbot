import os
import shutil
import ast
import uuid
import re
from typing import Union, BinaryIO, TextIO


class PatchApplierError(Exception):
    """Кастомное исключение для модуля PatchApplier."""
    pass


class PatchApplier:
    def __init__(self, repo_path: str, backup_dir: str = None):
        self.repo_path = repo_path
        self.backup_dir = backup_dir or repo_path

    def validate_patch_syntax(self, patch_content: str) -> bool:
        try:
            ast.parse(patch_content)
            return True
        except SyntaxError as e:
            raise PatchApplierError(f"Invalid syntax: {e}")

    def read_patch_stream(self, stream: Union[str, bytes, TextIO, BinaryIO]) -> str:
        if isinstance(stream, str):
            return stream
        if isinstance(stream, bytes):
            try:
                return stream.decode('utf-8')
            except UnicodeDecodeError as e:
                raise PatchApplierError(f"Binary stream rejection: {e}")
        if hasattr(stream, 'read'):
            content = stream.read()
            if isinstance(content, bytes):
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError as e:
                    raise PatchApplierError(f"Binary stream rejection: {e}")
            return str(content)
        raise PatchApplierError(f"Unsupported stream type: {type(stream)}")

    def dry_run(self, target_file_path: str, patch_content: str) -> bool:
        final_path = target_file_path
        if os.path.isdir(target_file_path):
            match = re.search(r'\+\+\+\s+(?:b/)?([^\t\n]+)', patch_content)
            if match:
                file_name = match.group(1).strip()
                final_path = os.path.join(target_file_path, file_name)
            else:
                files = os.listdir(target_file_path)
                if files:
                    final_path = os.path.join(target_file_path, files[0])

        if not os.path.exists(final_path):
            raise PatchApplierError(f"File not found: {final_path}")

        try:
            with open(final_path, 'r', encoding='utf-8') as f:
                f.read()
        except UnicodeDecodeError:
            raise PatchApplierError("Binary patch rejection: cannot decode as utf-8")
        except IOError as e:
            raise PatchApplierError(f"IO error: {e}")

        return True

    def apply_patch(self, target_file_path: str, patch_content: str) -> bool:
        final_path = target_file_path
        if os.path.isdir(target_file_path):
            match = re.search(r'\+\+\+\s+(?:b/)?([^\t\n]+)', patch_content)
            if match:
                file_name = match.group(1).strip()
                final_path = os.path.join(target_file_path, file_name)
            else:
                files = os.listdir(target_file_path)
                if files:
                    final_path = os.path.join(target_file_path, files[0])

        if not os.path.exists(final_path):
            raise PatchApplierError(f"File not found: {final_path}")

        try:
            with open(final_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
        except UnicodeDecodeError:
            raise PatchApplierError("Binary patch rejection: cannot decode as utf-8")
        except IOError as e:
            raise PatchApplierError(f"IO error: {e}")

        new_text = original_text
        if patch_content.startswith('---') or '@@' in patch_content:
            added_lines = []
            for line in patch_content.splitlines():
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines.append(line[1:])
            if added_lines:
                new_text = original_text + "\n" + "\n".join(added_lines) + "\n"
        else:
            new_text = patch_content

        try:
            with open(final_path, 'w', encoding='utf-8') as f:
                f.write(new_text)
        except IOError as e:
            raise PatchApplierError(f"IO error: {e}")

        return True

    def apply_patch_with_backup(self, target_file_path: str, patch_content: str) -> bool:
        if os.path.exists(target_file_path):
            backup_dir = self.backup_dir or os.path.dirname(target_file_path)
            os.makedirs(backup_dir, exist_ok=True)
            backup_filename = f"{os.path.basename(target_file_path)}.bak_{uuid.uuid4().hex[:4]}" if hasattr(uuid, 'uuid4') else f"{os.path.basename(target_file_path)}.bak"
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy(target_file_path, backup_path)
        return self.apply_patch(target_file_path, patch_content)

    def rollback(self, backup_path: str, target_file_path: str) -> bool:
        if not os.path.exists(backup_path):
            raise PatchApplierError(f"Backup file not found: {backup_path}")
        try:
            shutil.copy(backup_path, target_file_path)
            return True
        except IOError as e:
            raise PatchApplierError(f"Rollback error: {e}")


def apply_patch(repo_path: str, patch_content: str) -> bool:
    applier = PatchApplier(repo_path)
    return applier.apply_patch(repo_path, patch_content)