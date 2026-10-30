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
            if "already exists" in err_msg.lower():
                return True
            raise PatchApplierError(f"Failed to create recovery point: {err_msg}")
        return True

    def apply_patch(self, patch_source: Union[str, bytes, Dict[str, Any], Any]) -> bool:
        """Применяет патч из файла, строки, байтов, потока или словаря."""
        if isinstance(patch_source, dict):
            return apply_patch(self.repo_path, patch_source)

        if hasattr(patch_source, "read"):
            try:
                patch_content = patch_source.read()
                if isinstance(patch_content, str):
                    patch_content = patch_content.encode("utf-8")
            except Exception as e:
                raise PatchApplierError(f"Failed to read patch stream: {e}") from e
        elif isinstance(patch_source, bytes):
            patch_content = patch_source
        elif isinstance(patch_source, str):
            patch_file_path = patch_source
            if not os.path.isabs(patch_file_path):
                potential_path = os.path.join(self.repo_path, patch_file_path)
                if os.path.exists(potential_path) and os.path.isfile(potential_path):
                    patch_file_path = potential_path

            if os.path.exists(patch_file_path) and os.path.isfile(patch_file_path):
                try:
                    with open(patch_file_path, "rb") as f:
                        patch_content = f.read()
                except Exception as e:
                    raise PatchApplierError(f"Failed to read patch file '{patch_file_path}': {e}") from e
            else:
                patch_content = patch_source.encode("utf-8")
        else:
            raise PatchApplierError(f"Unsupported patch source type: {type(patch_source)}")

        cmd = ["git", "-C", self.repo_path, "apply"]
        res = subprocess.run(cmd, input=patch_content, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Failed to apply patch: {err_msg}")
        return True

    def rollback(self, backup_tag: str) -> bool:
        """Откатывает изменения к точке восстановления."""
        cmd = ["git", "-C", self.repo_path, "checkout", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Failed to rollback: {err_msg}")
        return True

    def verify_repository_state(self) -> bool:
        """Проверяет, что репозиторий находится в корректном состоянии."""
        cmd = ["git", "-C", self.repo_path, "status", "--porcelain"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0 or len(res.stdout.strip()) > 0:
            output = res.stdout.decode("utf-8", errors="ignore")
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
    if not isinstance(patch_data, dict):
        raise PatchApplierError(f"Expected dict for patch_data, got {type(patch_data)}")

    file_path = patch_data.get("file_path") or patch_data.get("target_file")
    if not file_path:
        raise PatchApplierError("Missing file_path in patch_data")

    content = patch_data.get("content")
    if content is None:
        content = patch_data.get("code") or patch_data.get("code_fragment", "")

    backup_id = patch_data.get("backup_id") or patch_data.get("backup_tag", "backup")

    applier = PatchApplier(repo_path)
    if backup_id:
        applier.create_recovery_point(backup_id)

    target_full_path = os.path.join(repo_path, file_path)
    os.makedirs(os.path.dirname(target_full_path), exist_ok=True)

    try:
        if isinstance(content, bytes):
            with open(target_full_path, "wb") as f:
                f.write(content)
        else:
            with open(target_full_path, "w", encoding="utf-8") as f:
                f.write(str(content))

        add_cmd = ["git", "-C", repo_path, "add", file_path]
        res_add = subprocess.run(add_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_add.returncode != 0:
            raise PatchApplierError(f"Failed to git add {file_path}: {res_add.stderr.decode('utf-8', errors='ignore')}")

        commit_cmd = ["git", "-C", repo_path, "commit", "-m", "Apply patch via PatchApplier"]
        res_commit = subprocess.run(commit_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_commit.returncode != 0:
            raise PatchApplierError(f"Failed to git commit: {res_commit.stderr.decode('utf-8', errors='ignore')}")

        applier.verify_repository_state()
    except Exception as e:
        if not isinstance(e, PatchApplierError):
            raise PatchApplierError(f"Failed to apply dictionary patch: {e}") from e
        raise e

    return True
