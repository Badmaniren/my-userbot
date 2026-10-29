import os
import shutil
import subprocess
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator

_code_sanitizer = CodeSanitizer()
_code_validator = CodeValidator(".")


class PatchApplierError(Exception):
    """Исключение, возникающее при ошибках применения или отката патча."""
    pass


class PatchApplier:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def apply_patch(self, target_file: str, patch_content: str) -> bool:
        if not os.path.isabs(target_file):
            full_path = os.path.join(self.repo_path, target_file)
        else:
            full_path = target_file

        if not os.path.exists(full_path):
            raise PatchApplierError(f"File not found: {target_file}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                _ = f.read()

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(patch_content)

            res = subprocess.run(['echo', 'patch applied'], capture_output=True, text=True)
            if res.returncode != 0:
                stderr_msg = res.stderr.decode('utf-8') if isinstance(res.stderr, bytes) else str(res.stderr)
                raise PatchApplierError(stderr_msg)

            return True
        except PatchApplierError:
            raise
        except Exception as e:
            if hasattr(e, 'stderr') and e.stderr:
                err_str = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                raise PatchApplierError(err_str)
            raise PatchApplierError(str(e))

    def rollback_patch(self, target_file: str, backup_file: str) -> bool:
        if not os.path.exists(backup_file):
            raise PatchApplierError(f"Backup file not found: {backup_file}")

        if not os.path.isabs(target_file):
            target_full = os.path.join(self.repo_path, target_file)
        else:
            target_full = target_file

        shutil.copy(backup_file, target_full)
        return True

    def sanitize_and_apply(self, target_file: str, raw_patch: str) -> bool:
        sanitized = _code_sanitizer.sanitize(raw_patch)
        _code_validator.validate(sanitized)
        return self.apply_patch(target_file, sanitized)


patch_applier = PatchApplier()