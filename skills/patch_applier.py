import os
import uuid
import subprocess
from typing import Dict, Any, Optional


class PatchApplierError(Exception):
    """Исключение, возникающее при ошибках применения патчей или управления репозиторием."""
    pass


class PatchApplier:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _ensure_git_repo(self):
        """Гарантирует инициализацию git репозитория при необходимости."""
        if os.path.exists(self.repo_path):
            dot_git = os.path.join(self.repo_path, ".git")
            if not os.path.exists(dot_git):
                try:
                    subprocess.run(["git", "-C", self.repo_path, "init"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception:
                    pass

    def create_recovery_point(self, backup_tag: str) -> bool:
        """Создает точку восстановления (ветку) в репозитории."""
        self._ensure_git_repo()
        cmd = ["git", "-C", self.repo_path, "branch", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            if "not a valid object name" in err_msg or "HEAD" in err_msg:
                # В сухом/пустом git-репозитории нет коммитов, создание ветки бэкапа не нужно
                return True
            raise PatchApplierError(f"Failed to create recovery point: {err_msg}")
        return True

    def apply_patch(self, patch_source: str) -> bool:
        """Применяет патч из файла, словаря или строки с содержимым патча."""
        if not isinstance(patch_source, str):
            raise PatchApplierError("Patch source must be a string.")

        patch_file_path = patch_source
        is_file = False

        if "\n" not in patch_source and "\r" not in patch_source:
            if not os.path.isabs(patch_file_path):
                potential_path = os.path.join(self.repo_path, patch_file_path)
                if os.path.exists(potential_path):
                    patch_file_path = potential_path

            if os.path.exists(patch_file_path) and os.path.isfile(patch_file_path):
                is_file = True

        if is_file:
            with open(patch_file_path, "rb") as f:
                patch_content = f.read()
            cmd = ["git", "-C", self.repo_path, "apply"]
            res = subprocess.run(cmd, input=patch_content, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif "\n" in patch_source or "\r" in patch_source or patch_source.startswith("diff ") or patch_source.startswith("---"):
            cmd = ["git", "-C", self.repo_path, "apply"]
            res = subprocess.run(cmd, input=patch_source, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            try:
                with open(patch_source, "rb") as f:
                    patch_content = f.read()
                cmd = ["git", "-C", self.repo_path, "apply"]
                res = subprocess.run(cmd, input=patch_content, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception:
                raise PatchApplierError("Patch source not found or invalid.")

        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore") if isinstance(res.stderr, bytes) else str(res.stderr)
            # Если файл из патча не существовал или синтаксис unified diff с ошибками (например, corrupt patch / no such file), пробуем применить созданием файла
            if ("No such file or directory" in err_msg or "corrupt patch" in err_msg) and ("--- a/" in patch_source or "+++ b/" in patch_source):
                try:
                    self._apply_diff_directly(patch_source)
                    return True
                except Exception as inner_e:
                    raise PatchApplierError(f"Failed to apply patch: {err_msg}") from inner_e
            raise PatchApplierError(f"Failed to apply patch: {err_msg}")
        return True

    def _apply_diff_directly(self, patch_source: str):
        """Интерпретирует простой unified diff и создает/обновляет target файлы."""
        lines = patch_source.splitlines()
        target_file = None
        new_lines = []
        for line in lines:
            if line.startswith("+++ b/"):
                target_file = line[6:].strip()
            elif target_file and (line.startswith("+") and not line.startswith("+++")):
                new_lines.append(line[1:])
            elif target_file and (line.startswith(" ") or (not line.startswith("-") and not line.startswith("@"))):
                new_lines.append(line)

        if target_file:
            full_path = os.path.join(self.repo_path, target_file)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")
        else:
            raise PatchApplierError("No valid target file in patch")

    def rollback(self, backup_tag: str) -> bool:
        """Откатывает изменения к точке восстановления."""
        self._ensure_git_repo()
        cmd = ["git", "-C", self.repo_path, "checkout", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            err_msg = res.stderr.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Failed to rollback: {err_msg}")
        return True

    def verify_repository_state(self) -> bool:
        """Проверяет, что репозиторий находится в корректном состоянии."""
        self._ensure_git_repo()
        cmd = ["git", "-C", self.repo_path, "status", "--porcelain"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            output = res.stdout.decode("utf-8", errors="ignore")
            raise PatchApplierError(f"Repository verification failed: {output}")
        return True

    def safe_apply(self, patch_path: str, backup_tag: Optional[str] = None) -> bool:
        """Безопасно применяет патч с созданием бэкапа и авто-откатом при ошибке."""
        if not backup_tag:
            backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
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
    
    with open(target_full_path, "w", encoding="utf-8") as f:
        f.write(content)

    applier = PatchApplier(repo_path)
    applier.create_recovery_point(backup_id)
    
    add_cmd = ["git", "-C", repo_path, "add", file_path]
    subprocess.run(add_cmd, check=True)
    
    commit_cmd = ["git", "-C", repo_path, "commit", "-m", "Apply patch via PatchApplier"]
    subprocess.run(commit_cmd, check=True)

    applier.verify_repository_state()
    return True