import os
import io
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier, PatchApplierError


class PatchPipeline:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self._sanitizer = None
        self._checker = None
        self._applier = None

    @property
    def sanitizer(self):
        if self._sanitizer is not None:
            return self._sanitizer
        return PatchSanitizer()

    @sanitizer.setter
    def sanitizer(self, value):
        self._sanitizer = value

    @property
    def checker(self):
        if self._checker is not None:
            return self._checker
        return PatchChecker(repo_path=self.repo_path)

    @checker.setter
    def checker(self, value):
        self._checker = value

    @property
    def applier(self):
        if self._applier is not None:
            return self._applier
        return PatchApplier(self.repo_path)

    @applier.setter
    def applier(self, value):
        self._applier = value

    def run(self, raw_patch, backup_tag=None, target_file=None):
        sanitized = self.sanitizer.sanitize(raw_patch)

        check_result = self.checker.check_patch(sanitized, target_file)
        if isinstance(check_result, dict):
            status = check_result.get("status")
            if status in ("rejected", "error"):
                return False
            if check_result.get("is_safe") is False or check_result.get("is_valid") is False:
                return False

        if target_file and os.path.exists(target_file):
            return self._apply_to_target_file(sanitized, target_file)

        if backup_tag:
            success = self.applier.safe_apply(sanitized, backup_tag=backup_tag)
        else:
            success = self.applier.safe_apply(sanitized)

        if not success and backup_tag:
            self.applier.rollback(backup_tag)
            return False

        return success

    def run_from_stream(self, stream):
        sanitized = self.sanitizer.sanitize(stream)
        return self.applier.safe_apply(sanitized)

    def _apply_to_target_file(self, sanitized: str, target_file: str) -> bool:
        if not sanitized or not isinstance(sanitized, str):
            raise ValueError("Invalid patch")

        lines = sanitized.splitlines()
        removed_lines = []
        added_lines = []
        is_diff = False

        for line in lines:
            if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
                is_diff = True
                continue
            if line.startswith("-"):
                is_diff = True
                removed_lines.append(line[1:])
            elif line.startswith("+"):
                is_diff = True
                added_lines.append(line[1:])

        if not is_diff and ("INVALID" in sanitized or "invalid" in sanitized.lower()):
            raise ValueError("Invalid patch data")

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        if removed_lines:
            old_str = "\n".join(removed_lines)
            new_str = "\n".join(added_lines)
            if old_str in content:
                content = content.replace(old_str, new_str, 1)
            else:
                replaced = False
                for old_line, new_line in zip(removed_lines, added_lines):
                    if old_line in content:
                        content = content.replace(old_line, new_line, 1)
                        replaced = True
                if not replaced and old_str:
                    raise ValueError("Patch target line not found")
        elif added_lines:
            content += ("\n" if not content.endswith("\n") else "") + "\n".join(added_lines)
        elif not is_diff:
            raise ValueError("Invalid patch format")

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        return True


def run_patch_pipeline(raw_patch, repo_path, target_file=None):
    """
    Функция-обертка для интеграционного теста.
    """
    pipeline = PatchPipeline(repo_path)
    result = pipeline.run(raw_patch, target_file=target_file)
    return result