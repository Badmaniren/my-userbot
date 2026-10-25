import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from pathlib import Path

from skills.anomaly_autofixer import AnomalyAutofixer, AnomalyAutofixerError


class TestAnomalyAutofixerInquisition(unittest.TestCase):

    def setUp(self):
        self.random_token = uuid.uuid4().hex
        self.random_path = Path(f"dir_{uuid.uuid4().hex[:6]}") / f"file_{uuid.uuid4().hex[:6]}.py"
        self.random_snippet = f"x_val_{uuid.uuid4().hex[:8]} = {random.randint(100, 999)}"

    def test_init_valid_parameters(self):
        fixer = AnomalyAutofixer(
            target_path=str(self.random_path),
            anti_cheat_token=self.random_token,
            audit_hub=MagicMock(),
            logger=MagicMock(),
            git_inspector=MagicMock()
        )
        self.assertEqual(fixer.target_path, str(self.random_path))
        self.assertEqual(fixer.anti_cheat_token, self.random_token)

    def test_init_invalid_empty_parameters(self):
        with self.assertRaises(AnomalyAutofixerError):
            AnomalyAutofixer(target_path="", anti_cheat_token=self.random_token)

        with self.assertRaises(AnomalyAutofixerError):
            AnomalyAutofixer(target_path=str(self.random_path), anti_cheat_token="")

    def test_apply_patch_string_valid_anti_cheat(self):
        fixer = AnomalyAutofixer(anti_cheat_token=self.random_token)
        payload = f"some prefix {self.random_token} random suffix {uuid.uuid4().hex}"
        result = fixer.apply_patch(payload)
        self.assertTrue(result)

    def test_apply_patch_string_invalid_anti_cheat(self):
        fixer = AnomalyAutofixer(anti_cheat_token=self.random_token)
        payload = f"completely unrelated payload {uuid.uuid4().hex}"
        result = fixer.apply_patch(payload)
        self.assertFalse(result)

    def test_apply_patch_string_empty_content(self):
        fixer = AnomalyAutofixer(anti_cheat_token=self.random_token)
        with self.assertRaises(AnomalyAutofixerError):
            fixer.apply_patch("")

    def test_apply_patch_dictionary_invalid_parameters(self):
        fixer = AnomalyAutofixer()
        invalid_dict = {"file_path": str(self.random_path)}
        with self.assertRaises(AnomalyAutofixerError):
            fixer.apply_patch(invalid_dict)

    def test_apply_patch_dictionary_integration_flow(self):
        mock_audit_hub = MagicMock()
        mock_audit_hub.repo_path = f"repo_{uuid.uuid4().hex[:6]}"

        mock_git_inspector = MagicMock()
        mock_git_inspector.repo_path = mock_audit_hub.repo_path

        fixer = AnomalyAutofixer(
            target_path=str(self.random_path),
            anti_cheat_token=self.random_token,
            audit_hub=mock_audit_hub,
            logger=MagicMock(),
            git_inspector=mock_git_inspector
        )

        patch_dict = {
            "file_path": f"anomaly_file_{uuid.uuid4().hex[:6]}.py",
            "fix_snippet": self.random_snippet
        }

        mock_path_instance = MagicMock(spec=Path)
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_text.return_value = f"# initial code {uuid.uuid4().hex}"

        with patch("skills.anomaly_autofixer.Path", return_value=mock_path_instance) as mock_path_class:
            result = fixer.apply_patch(patch_dict)
            self.assertTrue(result)
            mock_path_instance.write_text.assert_called_once()
            written_content = mock_path_instance.write_text.call_args[0][0]
            self.assertIn(self.random_snippet, written_content)