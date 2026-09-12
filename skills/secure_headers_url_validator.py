from skills import url_cleaner, headers_rotator

class SecureHeadersURLValidator:
    """
    Модуль для валидации URL-адресов с очисткой параметров и ротацией заголовков.
    """

    def __init__(self):
        self.rotator = headers_rotator.HeadersRotator()

    def validate(self, url: str, timeout: int = 5) -> bool:
        """
        Валидирует URL путем очистки и проверки заголовков.
        """
        try:
            cleaned_url = url_cleaner.clean_url(url)
            self.rotator.rotate_headers()
            return self.rotator.validate_headers_against_target(cleaned_url, timeout)
        except Exception:
            return False

    def validate_url(self, url: str, timeout: int = 5) -> bool:
        """
        Интеграционный метод для валидации URL (с предварительной очисткой).
        """
        try:
            cleaned_url = url_cleaner.clean_url(url)
            self.rotator.rotate_headers()
            return self.rotator.validate_headers_against_target(cleaned_url, timeout)
        except Exception:
            return False

    def check_target_security(self, url: str, timeout: int = 10) -> bool:
        """
        Проверка безопасности целевого URL через ротацию заголовков.
        """
        try:
            cleaned_url = url_cleaner.clean_url(url)
            self.rotator.rotate_headers()
            return self.rotator.validate_headers_against_target(cleaned_url, timeout)
        except Exception:
            return False

# Алиас для соответствия интеграционным тестам
SecureHeadersUrlValidator = SecureHeadersURLValidator