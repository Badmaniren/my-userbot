import os
import re
import shutil
import tempfile
import uuid


class PatchApplierError(Exception):
    pass


class PatchApplier:
    def __init__(self, backup_dir=None):
        if backup_dir is None:
            self.backup_dir = tempfile.mkdtemp(prefix="patch_backups_")
        else:
            self.backup_dir = backup_dir
            os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, file_path):
        if not os.path.exists(file_path):
            raise PatchApplierError(f"Cannot backup non-existent file: {file_path}")
        backup_filename = (
            f"{os.path.basename(file_path)}_{uuid.uuid4().hex}.bak"
        )
        backup_path = os.path.join(self.backup_dir, backup_filename)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def rollback(self, file_path, backup_path):
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, file_path)
            except Exception as e:
                raise PatchApplierError(f"Failed to rollback file: {e}") from e

    def _parse_and_apply(self, original_lines, diff_text):
        diff_lines = diff_text.splitlines()

        hunk_indices = [
            i
            for i, line in enumerate(diff_lines)
            if line.startswith("@@")
        ]

        if not hunk_indices:
            raise PatchApplierError("Invalid diff format: no hunk headers found.")

        header_found = False
        for line in diff_lines:
            if line.startswith("--- ") or line.startswith("+++ "):
                header_found = True
                break
        if not header_found:
            raise PatchApplierError("Invalid diff format: missing file headers.")

        hunks = []
        for idx, h_start in enumerate(hunk_indices):
            h_end = (
                hunk_indices[idx + 1]
                if idx + 1 < len(hunk_indices)
                else len(diff_lines)
            )
            hunk_header = diff_lines[h_start]
            match = re.match(r"^@@\s*-(\d+)(?:,(\d+))?\s*\+(\d+)(?:,(\d+))?\s*@@", hunk_header)
            if not match:
                raise PatchApplierError(f"Invalid hunk header format: {hunk_header}")

            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) is not None else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) is not None else 1

            hunk_body = diff_lines[h_start + 1 : h_end]
            hunks.append({
                "old_start": old_start,
                "old_count": old_count,
                "new_start": new_start,
                "new_count": new_count,
                "lines": hunk_body,
            })

        result = list(original_lines)
        offset = 0

        for hunk in hunks:
            old_start = hunk["old_start"]
            expected_old_lines = []
            new_lines = []

            for line in hunk["lines"]:
                if not line:
                    line = " "
                prefix = line[0]
                text = line[1:]
                if prefix == " ":
                    expected_old_lines.append(text)
                    new_lines.append(text)
                elif prefix == "-":
                    expected_old_lines.append(text)
                elif prefix == "+":
                    new_lines.append(text)
                elif prefix == "\\":
                    pass
                else:
                    raise PatchApplierError(f"Malformed hunk line: {line}")

            match_idx = -1
            target_start = (old_start - 1) + offset

            # Strategy 1: Check at target position
            if 0 <= target_start <= len(result):
                sub = result[target_start : target_start + len(expected_old_lines)]
                if sub == expected_old_lines:
                    match_idx = target_start

            # Strategy 2: Search anywhere if not matching target position
            if match_idx == -1 and expected_old_lines:
                for i in range(len(result) - len(expected_old_lines) + 1):
                    if result[i : i + len(expected_old_lines)] == expected_old_lines:
                        match_idx = i
                        break

            # Strategy 3: Prefix matching when lines partially match
            if match_idx == -1 and expected_old_lines:
                for i in range(len(result) - len(expected_old_lines) + 1):
                    match = True
                    for j, exp in enumerate(expected_old_lines):
                        act = result[i + j]
                        if act != exp and not act.startswith(exp):
                            match = False
                            break
                    if match:
                        match_idx = i
                        break

            if match_idx == -1 and expected_old_lines:
                raise PatchApplierError("Hunk could not be matched to file content.")

            if match_idx == -1 and not expected_old_lines:
                match_idx = target_start

            result[match_idx : match_idx + len(expected_old_lines)] = new_lines
            offset += len(new_lines) - len(expected_old_lines)

        return result

    def apply_patch(self, file_path, diff_text, dry_run=False, backup=True):
        if not os.path.exists(file_path):
            raise PatchApplierError(f"Target file does not exist: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise PatchApplierError(f"Failed to read file: {e}")

        orig_has_trailing_newline = content.endswith("\n") if content else True
        original_lines = content.splitlines()

        try:
            new_lines = self._parse_and_apply(original_lines, diff_text)
        except PatchApplierError:
            if dry_run:
                return False
            raise

        if dry_run:
            return True

        backup_file = None
        if backup:
            backup_file = self.create_backup(file_path)

        new_content = "\n".join(new_lines)
        if (orig_has_trailing_newline or new_lines) and not new_content.endswith("\n"):
            new_content += "\n"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            if backup_file:
                try:
                    self.rollback(file_path, backup_file)
                except Exception:
                    pass
            raise PatchApplierError(f"Failed to write patched file: {e}")

        return True


def apply_patch(file_path, patch_content, dry_run=False, backup=True):
    applier = PatchApplier()
    try:
        res = applier.apply_patch(file_path, patch_content, dry_run=dry_run, backup=backup)
        if res is True:
            return True
        return False
    except PatchApplierError:
        return False