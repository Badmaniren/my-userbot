import os
import subprocess
from typing import Dict, Any, Union


class PatchApplierError(Exception):
    """Исключение, возникающее при ошибках применения патчей или управления репозиторием."""
    pass


class PatchApplier:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def create_recovery_point(self, backup_tag: str) -> bool:
        """Создает точку восстановления (ветку) в репозитории."""
        cmd = ["git", "-C", self.repo_path, "branch", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Failed to create recovery point: {err_msg}")
        return True

    def apply_patch(self, patch_source: Union[str, bytes, Dict[str, Any]]) -> bool:
        """Применяет патч из файла, словаря или строки/байтов."""
        if isinstance(patch_source, dict):
            backup_id = patch_source.get("backup_id")
            if backup_id:
                self.create_recovery_point(backup_id)
            file_path = patch_source.get("file_path") or patch_source.get("path") or patch_source.get("target_file")
            content = patch_source.get("content", "")
            if file_path:
                target_full_path = os.path.join(self.repo_path, file_path)
                os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
                mode = "wb" if isinstance(content, bytes) else "w"
                encoding = None if isinstance(content, bytes) else "utf-8"
                with open(target_full_path, mode, encoding=encoding) as f:
                    f.write(content)
                add_cmd = ["git", "-C", self.repo_path, "add", file_path]
                subprocess.run(add_cmd, check=True)
                commit_cmd = ["git", "-C", self.repo_path, "commit", "-m", "Apply patch via PatchApplier"]
                subprocess.run(commit_cmd, check=True)
                self.verify_repository_state()
                return True

        if isinstance(patch_source, bytes):
            patch_content = patch_source
        elif isinstance(patch_source, str):
            patch_file_path = patch_source
            if not os.path.isabs(patch_file_path):
                potential_path = os.path.join(self.repo_path, patch_file_path)
                if os.path.exists(potential_path):
                    patch_file_path = potential_path

            if os.path.exists(patch_file_path) and os.path.isfile(patch_file_path):
                with open(patch_file_path, "rb") as f:
                    patch_content = f.read()
            elif "\n" in patch_source or "diff " in patch_source or "--- " in patch_source:
                patch_content = patch_source.encode("utf-8")
            else:
                if not os.path.exists(patch_file_path):
                    raise PatchApplierError(f"Failed to apply patch: file not found {patch_source}")
                with open(patch_file_path, "rb") as f:
                    patch_content = f.read()
        else:
            raise PatchApplierError(f"Unsupported patch_source type: {type(patch_source)}")

        cmd = ["git", "-C", self.repo_path, "apply"]
        res = subprocess.run(cmd, input=patch_content, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Failed to apply patch: {err_msg}")

        subprocess.run(["git", "-C", self.repo_path, "add", "-u"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Apply patch via PatchApplier"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True

    def rollback(self, backup_tag: str) -> bool:
        """Откатывает изменения к точке восстановления (сбрасывая индекс/воркдир и чекаутя ветку/коммит)."""
        subprocess.run(["git", "-C", self.repo_path, "reset", "--hard"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "clean", "-fd"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        cmd = ["git", "-C", self.repo_path, "checkout", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Failed to rollback: {err_msg}")
        return True

    def verify_repository_state(self) -> bool:
        """Проверяет, что репозиторий находится в корректном состоянии."""
        cmd = ["git", "-C", self.repo_path, "status", "--porcelain", "-uno"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0 or len(res.stdout.strip()) > 0:
            output = res.stdout.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Repository verification failed: {output}")
        return True

    def safe_apply(self, patch_path: Union[str, bytes, Dict[str, Any]], backup_tag: str) -> bool:
        """Безопасно применяет патч с созданием бэкапа и авто-откатом при ошибке."""
        self.create_recovery_point(backup_tag)
        try:
            self.apply_patch(patch_path)
            self.verify_repository_state()
        except Exception:
            self.rollback(backup_tag)
            raise
        return True


def apply_patch(repo_path: str, patch_data: Dict[str, Any]) -> bool:
    """Интеграционная функция для применения патча из словаря."""
    applier = PatchApplier(repo_path)
    return applier.apply_patch(patch_data)
