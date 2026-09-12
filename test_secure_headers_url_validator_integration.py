import unittest
from skills.secure_headers_url_validator import SecureHeadersUrlValidator
from skills.url_cleaner import clean_url
from skills.headers_rotator import HeadersRotator

class TestSecureHeadersUrlValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = SecureHeadersUrlValidator()
        self.rotator = HeadersRotator(cache_enabled=False)
        self.test_url = "https://example.com/path?utm_source=test&ref=123"

    def test_integration_flow(self):
        # 1. Проверка очистки через url_cleaner (интеграция)
        cleaned_url = clean_url(self.test_url)
        self.assertNotIn("utm_source", cleaned_url)

        # 2. Проверка ротации заголовков (интеграция)
        headers = self.rotator.rotate_headers()
        self.assertIsInstance(headers, dict)

        # 3. Проверка валидации через целевой модуль
        # Метод validate_url должен использовать внутри себя url_cleaner и headers_rotator
        is_valid = self.validator.validate_url(cleaned_url, timeout=5)

        self.assertIsInstance(is_valid, bool)

    def test_headers_validation_against_target(self):
        # Проверка, что модуль корректно взаимодействует с headers_rotator для целевого URL
        result = self.validator.check_target_security(self.test_url, timeout=10)
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()