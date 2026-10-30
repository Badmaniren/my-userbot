import os
import subprocess
from typing import Dict, Any


class PatchApplierError(Exception):
    """Исключение, возникающее при ошибках применения патчей или управления репозиторием."""
    pass


class PatchApplier:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def create_recovery_point(self, backup_tag: str) -> bool:
        """Создает точку восстановления (ветку) в репозитории."""
        cmd = ["git", "-C", self.repo_path, "branch", "-f", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore") if hasattr(res.stderr, "decode") else str(res.stderr)
            raise PatchApplierError(f"Failed to create recovery point: {err_msg}")
        return True

    def apply_patch(self, patch_source: str) -> bool:
        """Применяет патч из файла или словаря/пути."""
        patch_file_path = patch_source
        if isinstance(patch_source, str) and not os.path.isabs(patch_file_path):
            potential_path = os.path.join(self.repo_path, patch_file_path)
            if os.path.exists(potential_path):
                patch_file_path = potential_path

        if isinstance(patch_file_path, str) and os.path.exists(patch_file_path) and os.path.isfile(patch_file_path):
            with open(patch_file_path, "rb") as f:
                patch_content = f.read()
            cmd = ["git", "-C", self.repo_path, "apply"]
            res = subprocess.run(cmd, input=patch_content, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            try:
                if isinstance(patch_source, bytes):
                    patch_content = patch_source
                elif isinstance(patch_source, str):
                    with open(patch_source, "rb") as f:
                        patch_content = f.read()
                else:
                    raise ValueError(f"Unsupported patch source type: {type(patch_source)}")
                cmd = ["git", "-C", self.repo_path, "apply"]
                res = subprocess.run(cmd, input=patch_content, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                raise PatchApplierError(f"Patch source not found or invalid: {e}")

        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore") if hasattr(res.stderr, "decode") else str(res.stderr)
            raise PatchApplierError(f"Failed to apply patch: {err_msg}")
        return True

    def rollback(self, backup_tag: str) -> bool:
        """Откатывает изменения к точке восстановления."""
        cmd = ["git", "-C", self.repo_path, "checkout", "-f", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore") if hasattr(res.stderr, "decode") else str(res.stderr)
            raise PatchApplierError(f"Failed to rollback: {err_msg}")

        clean_cmd = ["git", "-C", self.repo_path, "clean", "-fd"]
        subprocess.run(clean_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True

    def verify_repository_state(self) -> bool:
        """Проверяет, что репозиторий находится в корректном состоянии."""
        cmd = ["git", "-C", self.repo_path, "status", "--porcelain"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if isinstance(res.stdout, bytes):
            output = res.stdout.decode("utf-8", errors="ignore").strip()
        elif isinstance(res.stdout, str):
            output = res.stdout.strip()
        else:
            output = ""

        if res.returncode != 0:
            raise PatchApplierError(f"Repository verification failed: {output}")
        if output:
            raise PatchApplierError(f"Repository verification failed: {output}")
        return True

    def safe_apply(self, patch_path: str, backup_tag: str) -> bool:
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
    file_path = patch_data.get("file_path")
    content = patch_data.get("content")
    backup_id = patch_data.get("backup_id", "backup")

    target_full_path = os.path.join(repo_path, file_path)

    os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
    with open(target_full_path, "w", encoding="utf-8") as f:
        f.write(content)

    applier = PatchApplier(repo_path)
    applier.create_recovery_point(backup_id)

    add_cmd = ["git", "-C", repo_path, "add", file_path]
    subprocess.run(add_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    commit_cmd = ["git", "-C", repo_path, "commit", "-m", "Apply patch via PatchApplier"]
    subprocess.run(commit_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    applier.verify_repository_state()
    return True
