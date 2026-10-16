import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.code_patcher import CodePatcher
from skills.code_validator import CodeValidator, CodeValidatorASTError
from skills.patch_executor import PatchExecutor, PatchExecutorError

class TestCodePatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patcher = CodePatcher(repo_path=self.repo_path)

    def test_apply_patch_success_flow(self):
        """Проверка успешной композиции: валидация проходит, патч исполняется."""
        random_code = "".join(random.choices(string.ascii_letters, k=50))
        random_patch_data = {"id": uuid.uuid4().hex, "content": random_code}

        with patch('skills.code_patcher.CodeValidator') as MockValidator, \
             patch('skills.code_patcher.PatchExecutor') as MockExecutor:

            validator_instance = MockValidator.return_value
            validator_instance.validate_patch_ast.return_value = True

            executor_instance = MockExecutor.return_value
            executor_instance.apply_patch.return_value = True

            result = self.patcher.apply_patch(random_patch_data)

            self.assertTrue(result)
            validator_instance.validate_patch_ast.assert_called_once_with(random_code)
            executor_instance.apply_patch.assert_called_once_with(random_patch_data)

    def test_apply_patch_validation_failure(self):
        """Проверка блокировки патча при ошибке валидации AST."""
        random_code = "".join(random.choices(string.ascii_letters, k=30))
        random_patch_data = {"id": uuid.uuid4().hex, "content": random_code}

        with patch('skills.code_patcher.CodeValidator') as MockValidator, \
             patch('skills.code_patcher.PatchExecutor') as MockExecutor:

            validator_instance = MockValidator.return_value
            validator_instance.validate_patch_ast.side_effect = CodeValidatorASTError("Invalid AST")

            executor_instance = MockExecutor.return_value

            with self.assertRaises(CodeValidatorASTError):
                self.patcher.apply_patch(random_patch_data)

            executor_instance.apply_patch.assert_not_called()

    def test_apply_patch_execution_failure(self):
        """Проверка корректной обработки исключения при сбое исполнителя."""
        random_code = "".join(random.choices(string.ascii_letters, k=40))
        random_patch_data = {"id": uuid.uuid4().hex, "content": random_code}

        with patch('skills.code_patcher.CodeValidator') as MockValidator, \
             patch('skills.code_patcher.PatchExecutor') as MockExecutor:

            validator_instance = MockValidator.return_value
            validator_instance.validate_patch_ast.return_value = True

            executor_instance = MockExecutor.return_value
            executor_instance.apply_patch.side_effect = PatchExecutorError("Execution failed")

            with self.assertRaises(PatchExecutorError):
                self.patcher.apply_patch(random_patch_data)

            validator_instance.validate_patch_ast.assert_called_once()

    def test_stream_validation_logic(self):
        """Проверка обработки потоковых данных через валидатор."""
        random_stream_content = b"".join([bytes([random.randint(0, 255)]) for _ in range(100)])
        stream = io.BytesIO(random_stream_content)

        with patch('skills.code_patcher.CodeValidator') as MockValidator:
            validator_instance = MockValidator.return_value
            validator_instance.validate_stream.return_value = True

            result = self.patcher.validate_stream(stream)

            self.assertTrue(result)
            validator_instance.validate_stream.assert_called_once()
            # Проверяем, что переданный поток был прочитан
            args, _ = validator_instance.validate_stream.call_args
            self.assertEqual(args[0].read(), b"") # Поток исчерпан

    def test_dependency_initialization(self):
        """Проверка, что CodePatcher корректно инициализирует зависимости с переданным путем."""
        with patch('skills.code_patcher.CodeValidator') as MockValidator, \
             patch('skills.code_patcher.PatchExecutor') as MockExecutor:

            _ = CodePatcher(repo_path=self.repo_path)

            MockValidator.assert_called_with(repo_path=self.repo_path)
            MockExecutor.assert_called()
            # Проверяем, что PatchExecutor получил нужные аргументы (repo_path)
            args, kwargs = MockExecutor.call_args
            self.assertEqual(kwargs['repo_path'], self.repo_path)

if __name__ == '__main__':
    unittest.main()