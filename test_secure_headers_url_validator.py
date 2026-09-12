import unittest
from unittest.mock import patch, MagicMock
from skills.secure_headers_url_validator import SecureHeadersURLValidator

class TestSecureHeadersURLValidator(unittest.TestCase):

    def setUp(self):
        self.validator = SecureHeadersURLValidator()
        self.test_url = "https://example.com/path?utm_source=test&ref=123"

    def test_validate_url_success(self):
        with patch('skills.url_cleaner.clean_url') as mock_cleaner, \
             patch('skills.headers_rotator.HeadersRotator.validate_headers_against_target') as mock_rotator:

            mock_cleaner.return_value = "https://example.com/path"
            mock_rotator.return_value = True

            result = self.validator.validate(self.test_url, timeout=5)
            self.assertTrue(result)
            mock_cleaner.assert_called_once_with(self.test_url)
            mock_rotator.assert_called_once()

    def test_validate_url_cleaner_failure(self):
        with patch('skills.url_cleaner.clean_url') as mock_cleaner:
            mock_cleaner.side_effect = Exception("Cleaning failed")

            result = self.validator.validate(self.test_url, timeout=5)
            self.assertFalse(result)

    def test_validate_url_rotator_failure(self):
        with patch('skills.url_cleaner.clean_url') as mock_cleaner, \
             patch('skills.headers_rotator.HeadersRotator.validate_headers_against_target') as mock_rotator:

            mock_cleaner.return_value = "https://example.com/path"
            mock_rotator.return_value = False

            result = self.validator.validate(self.test_url, timeout=5)
            self.assertFalse(result)

    def test_validate_url_exception_handling(self):
        with patch('skills.headers_rotator.HeadersRotator.validate_headers_against_target') as mock_rotator:
            mock_rotator.side_effect = ConnectionError("Network unreachable")

            result = self.validator.validate(self.test_url, timeout=5)
            self.assertFalse(result)

    def test_normalization_integration(self):
        with patch('skills.url_cleaner.clean_url') as mock_cleaner, \
             patch('skills.headers_rotator.HeadersRotator.validate_headers_against_target') as mock_rotator:

            mock_cleaner.return_value = "https://example.com/path"
            mock_rotator.return_value = True

            self.validator.validate(self.test_url, timeout=10)

            # Verify that the cleaner was called before the rotator
            mock_cleaner.assert_called_once()
            args, _ = mock_rotator.call_args
            self.assertEqual(args[0], "https://example.com/path")

    def test_invalid_url_format(self):
        with patch('skills.url_cleaner.clean_url') as mock_cleaner:
            mock_cleaner.side_effect = ValueError("Invalid URL")

            result = self.validator.validate("not_a_url", timeout=5)
            self.assertFalse(result)

    def test_headers_rotation_logic(self):
        with patch('skills.url_cleaner.clean_url') as mock_cleaner, \
             patch('skills.headers_rotator.HeadersRotator') as mock_rotator_class:

            mock_instance = mock_rotator_class.return_value
            mock_instance.validate_headers_against_target.return_value = True
            mock_cleaner.return_value = "https://example.com"

            validator = SecureHeadersURLValidator()
            validator.validate(self.test_url, timeout=5)

            mock_instance.rotate_headers.assert_called()
            mock_instance.validate_headers_against_target.assert_called_with("https://example.com", 5)

if __name__ == '__main__':
    unittest.main()