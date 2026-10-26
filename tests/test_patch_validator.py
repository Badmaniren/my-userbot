import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.patch_validator import PatchValidator, PatchValidatorError

class TestPatchValidator(unittest.TestCase):

    def setUp(self):
        self.validator = PatchValidator()
        self.random_id = uuid.uuid4().hex
        self.random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"
        self.random_content = ''.join(random.choices(string.ascii_letters + string.digits, k=128))

    def test_validate_structure_success(self):
        """Проверка корректной структуры патча с рандомными данными."""
        mock_patch_data = {
            "id": self.random_id,
            "payload": self.random_content,
            "checksum": uuid.uuid4().hex
        }

        result = self.validator.validate_structure(mock_patch_data)
        self.assertTrue(result)

    def test_validate_structure_failure(self):
        """Проверка выброса исключения при битой структуре."""
        invalid_data = {"wrong_key": self.random_id}
        with self.assertRaises(PatchValidatorError):
            self.validator.validate_structure(invalid_data)

    def test_safety_check_integration(self):
        """Проверка интеграции с системой безопасности через моки."""
        with patch('skills.patch_validator.CodeSanitizer') as mock_sanitizer:
            instance = mock_sanitizer.return_value
            instance.is_safe.return_value = True

            test_input = f"def {uuid.uuid4().hex}(): pass"
            is_safe = self.validator.verify_safety(test_input)

            self.assertTrue(is_safe)
            instance.is_safe.assert_called_once_with(test_input)

    def test_patch_integrity_with_telemetry(self):
        """Проверка целостности с использованием телеметрии."""
        random_metric = uuid.uuid4().hex
        random_val = random.randint(1, 1000)

        with patch('skills.patch_validator.SystemTelemetry') as mock_telemetry:
            mock_inst = mock_telemetry.return_value

            self.validator.check_integrity(self.random_path, telemetry=mock_inst)

            mock_inst.log_event.assert_called()
            args, _ = mock_inst.log_event.call_args
            self.assertIn(self.random_path, args)

    def test_complex_validation_flow(self):
        """Сквозная проверка валидации с рандомным потоком данных."""
        random_buffer = io.BytesIO(self.random_content.encode('utf-8'))

        with patch('skills.patch_validator.open', return_value=random_buffer):
            with patch('skills.patch_validator.PatchChecker') as mock_checker:
                checker_instance = mock_checker.return_value
                checker_instance.check.return_value = True

                result = self.validator.full_validate(self.random_path)

                self.assertTrue(result)
                checker_instance.check.assert_called_once()

    def test_error_handling_on_corrupted_file(self):
        """Проверка обработки ошибок при чтении поврежденного файла."""
        with patch('skills.patch_validator.open', side_effect=IOError("Access Denied")):
            with self.assertRaises(PatchValidatorError):
                self.validator.full_validate(self.random_path)

    def test_anomaly_reporting_on_invalid_patch(self):
        """Проверка отправки аномалии при обнаружении опасного патча."""
        with patch('skills.patch_validator.AnomalyAuditHub') as mock_hub:
            hub_instance = mock_hub.return_value

            # Имитируем обнаружение опасного кода
            with patch('skills.patch_validator.CodeSanitizer.is_safe', return_value=False):
                self.validator.verify_safety(self.random_content)

                hub_instance.log_anomaly.assert_called_once()
                args, kwargs = hub_instance.log_anomaly.call_args
                self.assertEqual(args[1], "CRITICAL")

if __name__ == '__main__':
    unittest.main()