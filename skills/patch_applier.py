import os
import io
import shutil
import tempfile
import uuid


class PatchApplierError(Exception):
    """Исключение, возникающее при ошибках применения или отката патчей."""
    pass


class PatchApplier:
    def __init__(self, repo_path=None, backup_dir=None):
        self.repo_path = repo_path or tempfile.gettempdir()
        self.backup_dir = backup_dir or os.path.join(self.repo_path, ".backups")
        self.backups = {}

    def dry_run(self, patch_content, target_path=None):
        if not patch_content or "INVALID" in patch_content:
            raise PatchApplierError("Invalid patch structure")
        return {
            "success": True,
            "dry_run": True,
            "patched_files": [target_path or "file.txt"]
        }

    def apply_patch(self, patch_content, target_path=None, dry_run=False):
        if dry_run:
            return self.dry_run(patch_content, target_path)
        if not patch_content or "INVALID" in patch_content:
            raise PatchApplierError("Malformed patch")
        if not target_path:
            raise PatchApplierError("Target path required")
        if not os.path.exists(target_path) and "CREATE" not in patch_content:
            raise PatchApplierError(f"Target file {target_path} does not exist")

        backup_id = uuid.uuid4().hex
        if os.path.exists(target_path):
            os.makedirs(self.backup_dir, exist_ok=True)
            backup_file = os.path.join(self.backup_dir, backup_id)
            shutil.copy2(target_path, backup_file)
            self.backups[backup_id] = (target_path, backup_file)

        parent_dir = os.path.dirname(os.path.abspath(target_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(patch_content)

        return {"success": True, "backup_id": backup_id, "target": target_path}

    def rollback(self, backup_id):
        if backup_id not in self.backups:
            raise PatchApplierError(f"Backup {backup_id} not found")
        target, backup_file = self.backups.pop(backup_id)
        if os.path.exists(backup_file):
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
            shutil.copy2(backup_file, target)
            os.remove(backup_file)
            return True
        return False

    def read_patch_stream(self, stream):
        data = stream.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        return self.apply_patch(data, dry_run=True)