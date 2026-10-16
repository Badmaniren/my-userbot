import unittest
from unittest.mock import MagicMock, patch
import io
import ast
import random
import uuid
from skills.patch_autocorrector import (
    PatchAutocorrector,
    PatchAutocorrectorError,
    PatchSyntaxError
)

class TestPatchAutocorrector(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.sanitizer_mock = MagicMock()
        self.validator_mock = MagicMock()
        self.autocorrector = PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer_mock,
            validator=self.validator_mock
        )

    def test_init_default_dependencies(self):
        corrector = PatchAutocorrector(repo_path=self.repo_path)
        self.assertEqual(corrector.repo_path, self.repo_path)
        self.assertIsNotNone(corrector.sanitizer)
        self.assertIsNotNone(corrector.validator)

    def test_correct_syntax_success(self):
        func_name = f"func_{uuid.uuid4().hex[:8]}"
        var_name = f"var_{uuid.uuid4().hex[:8]}"
        val = random.randint(100, 999)
        valid_code = f"def {func_name}():\n    {var_name} = {val}\n    return {var_name}"
        
        result = self.autocorrector.correct_syntax(valid_code)
        self.assertEqual(result, valid_code)

    def test_correct_syntax_raises_error_on_fatal_syntax(self):
        invalid_code = f"def {uuid.uuid4().hex}():\n    print({random.randint(1, 10)}"
        with self.assertRaises(PatchSyntaxError):
            self.autocorrector.correct_syntax(invalid_code)

    def test_apply_transformations_returns_original(self):
        random_code = f"x = {random.randint(10, 50)}"
        res = self.autocorrector._apply_transformations(random_code)
        self.assertEqual(res, random_code)

    def test_transform_stream_bytes(self):
        val = random.randint(1, 100)
        code_content = f"a = {val}".encode('utf-8')
        stream = io.BytesIO(code_content)
        
        transformed = self.autocorrector.transform_stream(stream)
        self.assertEqual(transformed, f"a = {val}")

    def test_transform_stream_string(self):
        val = random.randint(101, 200)
        code_content = f"b = {val}"
        stream = io.StringIO(code_content)
        
        transformed = self.autocorrector.transform_stream(stream)
        self.assertEqual(transformed, code_content)

    def test_transform_stream_raises_error_on_bad_stream(self):
        bad_stream = MagicMock()
        bad_stream.read.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(PatchAutocorrectorError):
            self.autocorrector.transform_stream(bad_stream)

    def test_batch_correct(self):
        key1 = uuid.uuid4().hex
        key2 = uuid.uuid4().hex
        val1 = random.randint(1, 50)
        val2 = random.randint(51, 100)
        
        batch = {
            key1: f"x = {val1}",
            key2: f"y = {val2}"
        }
        
        results = self.autocorrector.batch_correct(batch)
        self.assertIn(key1, results)
        self.assertIn(key2, results)
        self.assertEqual(results[key1], f"x = {val1}")
        self.assertEqual(results[key2], f"y = {val2}")

    def test_batch_correct_raises_on_invalid(self):
        key = uuid.uuid4().hex
        batch = {
            key: f"def {uuid.uuid4().hex}("
        }
        with self.assertRaises(PatchSyntaxError):
            self.autocorrector.batch_correct(batch)

    def test_correct_and_validate(self):
        val = random.randint(1000, 9999)
        code = f"result = {val}"
        res = self.autocorrector.correct_and_validate(code)
        self.assertEqual(res, code)

    def test_process_and_verify(self):
        file_name = f"{uuid.uuid4().hex}.py"
        code_fragment = f"print('{uuid.uuid4().hex}')"
        expected_result = random.choice([True, False])

        with patch("skills.patch_autocorrector.PatchVerifier") as mock_verifier_cls:
            mock_verifier_instance = mock_verifier_cls.return_value
            mock_verifier_instance.verify_and_apply.return_value = expected_result

            res = self.autocorrector.process_and_verify(file_name, code_fragment)
            
            mock_verifier_cls.assert_called_once_with(self.repo_path)
            mock_verifier_instance.verify_and_apply.assert_called_once_with(file_name, code_fragment)
            self.assertEqual(res, expected_result)