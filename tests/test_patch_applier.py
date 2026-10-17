import io
import os
import random
import shutil
import string
import tempfile
import unittest
from unittest.mock import patch, mock_open

from skills.patch_applier import PatchApplier, PatchApplierError


def _rand_str(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def _generate_unified_diff(file_path, old_lines, new_lines):
    rel_path = os.path.basename(file_path)
    hunk_header = f"@@ -1,{len(old_lines)} +1,{len(new_lines)} @@"
    diff_lines = [
        f"--- a/{rel_path}",
        f"+++ b/{rel_path}",
        hunk_header
    ]
    for line in old_lines:
        diff_lines.append(f"-{line}")
    for line in new_lines:
        diff_lines.append(f"+{line}")
    return "\n".join(diff_lines) + "\n"


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"test_patch_{_rand_str(6)}_")
        self.backup_dir = os.path.join(self.test_dir, f"backups_{_rand_str(6)}")
        self.applier = PatchApplier(backup_dir=self.backup_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_temp_file(self, content):
        file_name = f"file_{_rand_str(8)}.txt"
        file_path = os.path.join(self.test_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def test_init_creates_backup_directory(self):
        rand_sub = os.path.join(self.test_dir, f"custom_backup_{_rand_str(8)}")
        self.assertFalse(os.path.exists(rand_sub))
        applier = PatchApplier(backup_dir=rand_sub)
        self.assertTrue(os.path.exists(applier.backup_dir))

    def test_apply_patch_success(self):
        token_a = f"alpha_{_rand_str(8)}"
        token_b = f"beta_{_rand_str(8)}"
        token_c = f"gamma_{_rand_str(8)}"
        replacement_token = f"delta_new_{_rand_str(8)}"

        orig_lines = [token_a, token_b, token_c]
        orig_content = "\n".join(orig_lines) + "\n"
        file_path = self._create_temp_file(orig_content)

        new_lines = [token_a, replacement_token, token_c]
        expected_content = "\n".join(new_lines) + "\n"

        diff_text = (
            f"--- a/{os.path.basename(file_path)}\n"
            f"+++ b/{os.path.basename(file_path)}\n"
            f"@@ -1,3 +1,3 @@\n"
            f" {token_a}\n"
            f"-{token_b}\n"
            f"+{replacement_token}\n"
            f" {token_c}\n"
        )

        result = self.applier.apply_patch(file_path, diff_text, dry_run=False)
        self.assertTrue(result)

        with open(file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertEqual(updated_content, expected_content)

    def test_dry_run_does_not_modify_file(self):
        token_orig = f"orig_{_rand_str(10)}"
        token_new = f"modified_{_rand_str(10)}"
        file_path = self._create_temp_file(token_orig + "\n")

        diff_text = _generate_unified_diff(file_path, [token_orig], [token_new])

        result = self.applier.apply_patch(file_path, diff_text, dry_run=True)
        self.assertTrue(result)

        with open(file_path, "r", encoding="utf-8") as f:
            content_after = f.read()

        self.assertEqual(content_after, token_orig + "\n")

    def test_backup_file_created_on_apply(self):
        token_orig = f"backup_test_{_rand_str(12)}"
        token_new = f"replacement_{_rand_str(12)}"
        file_path = self._create_temp_file(token_orig + "\n")

        diff_text = _generate_unified_diff(file_path, [token_orig], [token_new])

        self.applier.apply_patch(file_path, diff_text, dry_run=False)

        backup_files = os.listdir(self.backup_dir)
        self.assertGreater(len(backup_files), 0)

        found_backup = False
        for b_name in backup_files:
            b_path = os.path.join(self.backup_dir, b_name)
            with open(b_path, "r", encoding="utf-8") as bf:
                if bf.read() == token_orig + "\n":
                    found_backup = True
                    break
        self.assertTrue(found_backup, "Backup file content must match original content before patch")

    def test_apply_patch_mismatch_raises_error_and_preserves_file(self):
        token_real = f"real_content_{_rand_str(10)}"
        token_fake = f"nonexistent_{_rand_str(10)}"
        token_new = f"target_{_rand_str(10)}"

        file_path = self._create_temp_file(token_real + "\n")
        bad_diff = _generate_unified_diff(file_path, [token_fake], [token_new])

        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(file_path, bad_diff, dry_run=False)

        with open(file_path, "r", encoding="utf-8") as f:
            content_after = f.read()

        self.assertEqual(content_after, token_real + "\n")

    def test_dry_run_mismatch_returns_false_or_raises_error(self):
        token_real = f"data_{_rand_str(8)}"
        token_wrong = f"wrong_{_rand_str(8)}"
        token_target = f"target_{_rand_str(8)}"

        file_path = self._create_temp_file(token_real + "\n")
        bad_diff = _generate_unified_diff(file_path, [token_wrong], [token_target])

        try:
            result = self.applier.apply_patch(file_path, bad_diff, dry_run=True)
            self.assertFalse(result)
        except PatchApplierError:
            pass

        with open(file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), token_real + "\n")

    def test_apply_patch_nonexistent_file_raises_error(self):
        non_existent = os.path.join(self.test_dir, f"missing_{_rand_str(8)}.txt")
        diff_text = f"--- a/missing\n+++ b/missing\n@@ -1 +1 @@\n-a\n+b\n"
        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(non_existent, diff_text)

    def test_apply_patch_invalid_diff_format_raises_error(self):
        garbage_diff = f"GARBAGE_DIFF_CONTENT_{_rand_str(32)}"
        file_path = self._create_temp_file(f"content_{_rand_str(10)}\n")

        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(file_path, garbage_diff)

    def test_rollback_on_write_failure(self):
        initial_token = f"immutable_token_{_rand_str(16)}"
        replacement_token = f"new_token_{_rand_str(16)}"
        file_path = self._create_temp_file(initial_token + "\n")

        diff_text = _generate_unified_diff(file_path, [initial_token], [replacement_token])

        # Simulate write failure during actual write phase
        orig_open = open

        def side_effect_open(path, mode="r", *args, **kwargs):
            if path == file_path and "w" in mode:
                raise IOError(f"Simulated disk failure: {_rand_str(6)}")
            return orig_open(path, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=side_effect_open):
            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(file_path, diff_text, dry_run=False)

        with open(file_path, "r", encoding="utf-8") as f:
            restored_content = f.read()

        self.assertEqual(restored_content, initial_token + "\n")

    def test_explicit_backup_and_rollback(self):
        original_token = f"token_pre_backup_{_rand_str(12)}"
        corrupted_token = f"token_corrupted_{_rand_str(12)}"
        file_path = self._create_temp_file(original_token + "\n")

        backup_file = self.applier.create_backup(file_path)
        self.assertTrue(os.path.exists(backup_file))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(corrupted_token + "\n")

        self.applier.rollback(file_path, backup_file)

        with open(file_path, "r", encoding="utf-8") as f:
            final_content = f.read()

        self.assertEqual(final_content, original_token + "\n")

    def test_multiline_complex_hunk_application(self):
        header = f"HEADER_{_rand_str(8)}"
        keep1 = f"KEEP1_{_rand_str(8)}"
        drop1 = f"DROP1_{_rand_str(8)}"
        add1 = f"ADD1_{_rand_str(8)}"
        keep2 = f"KEEP2_{_rand_str(8)}"
        footer = f"FOOTER_{_rand_str(8)}"

        orig_lines = [header, keep1, drop1, keep2, footer]
        file_path = self._create_temp_file("\n".join(orig_lines) + "\n")

        diff_text = (
            f"--- a/{os.path.basename(file_path)}\n"
            f"+++ b/{os.path.basename(file_path)}\n"
            f"@@ -1,5 +1,5 @@\n"
            f" {header}\n"
            f" {keep1}\n"
            f"-{drop1}\n"
            f"+{add1}\n"
            f" {keep2}\n"
            f" {footer}\n"
        )

        res = self.applier.apply_patch(file_path, diff_text, dry_run=False)
        self.assertTrue(res)

        expected_lines = [header, keep1, add1, keep2, footer]
        with open(file_path, "r", encoding="utf-8") as f:
            applied_lines = [line.strip() for line in f if line.strip()]

        self.assertEqual(applied_lines, expected_lines)

    def test_stream_reading_patch(self):
        token_a = f"stream_a_{_rand_str(8)}"
        token_b = f"stream_b_{_rand_str(8)}"
        file_path = self._create_temp_file(token_a + "\n")
        diff_text = _generate_unified_diff(file_path, [token_a], [token_b])

        fake_stream = io.StringIO(diff_text)
        read_patch = fake_stream.read()

        res = self.applier.apply_patch(file_path, read_patch, dry_run=False)
        self.assertTrue(res)

        with open(file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), token_b + "\n")


if __name__ == "__main__":
    unittest.main()