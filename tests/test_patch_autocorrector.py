import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import string

from skills.patch_autocorrector import (
    PatchAutocorrectorError,
    PatchSyntaxError,
    PatchAutocorrector
)

class TestPatchAutocorrector(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.autocorrector = PatchAutocorrector(self.repo_path)

    def test_init_sets_repo_path(self):
        self.assertEqual(self.autocorrector.repo_path, self.repo_path)

    def test_correct_patch_syntax_success(self):
        random_var = f"var_{uuid.uuid4().hex[:6]}"
        random_val = random.randint(100, 999)
        input_code = f"{random_var} = {random_val}\n"
        
        corrected = self.autocorrector.correct_syntax(input_code)
        
        self.assertIn(random_var, corrected)
        self.assertIn(str(random_val), corrected)

    def test_correct_patch_syntax_raises_error_on_fatal_syntax(self):
        corrupted_code = f"def {uuid.uuid4().hex()}(:\n    print({random.randint(1, 10)})"
        
        with self.assertRaises(PatchSyntaxError):
            self.autocorrector.correct_syntax(corrupted_code)

    def test_transform_patch_content(self):
        target_word = uuid.uuid4().hex
        replacement_word = uuid.uuid4().hex
        
        input_stream = io.BytesIO(f"def {uuid.uuid4().hex}():\n    return '{target_word}'".encode('utf-8'))
        
        with patch('skills.patch_autocorrector.PatchAutocorrector._apply_transformations') as mock_transform:
            mock_transform.return_value = f"def func():\n    return '{replacement_word}'"
            
            result = self.autocorrector.transform_stream(input_stream)
            
            self.assertIn(replacement_word, result)
            mock_transform.assert_called_once()

    def test_batch_correct_patches(self):
        batch_id = uuid.uuid4().hex
        patch_keys = [uuid.uuid4().hex for _ in range(3)]
        patch_dict = {key: f"x_{i} = {random.randint(1, 50)}" for i, key in enumerate(patch_keys)}
        
        results = self.autocorrector.batch_correct(patch_dict)
        
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), len(patch_keys))
        for key in patch_keys:
            self.assertIn(key, results)
            self.assertIsInstance(results[key], str)

    def test_autocorrect_integration_with_verifier_mock(self):
        file_name = f"{uuid.uuid4().hex}.py"
        code_fragment = f"class {uuid.uuid4().hex[:8].capitalize()}:\n    PASS_FLAG = {random.choice([True, False])}"
        
        with patch('skills.patch_autocorrector.PatchVerifier') as MockVerifier:
            instance = MockVerifier.return_value
            instance.verify_and_apply.return_value = True
            
            outcome = self.autocorrector.process_and_verify(file_name, code_fragment)
            
            self.assertTrue(outcome)
            instance.verify_and_apply.assert_called_once()

    def test_autocorrect_handles_exception_during_stream_read(self):
        bad_stream = MagicMock()
        bad_stream.read.side_effect = IOError(uuid.uuid4().hex)
        
        with self.assertRaises(PatchAutocorrectorError):
            self.autocorrector.transform_stream(bad_stream)