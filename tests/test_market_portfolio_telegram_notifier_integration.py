import unittest
import uuid
import random
from skills.market_portfolio_telegram_notifier import start_new

class TestTelegramNotifierIntegration(unittest.TestCase):
    """
    Интеграционный тест для проверки взаимодействия с Telegram API.
    Использует реальные сетевые вызовы без моков.
    """

    def setUp(self):
        # Генерируем случайные данные для каждого запуска, чтобы избежать кэширования и хардкода
        self.test_token = f"123456:ABC-DEF{uuid.uuid4().hex[:10]}"
        self.test_chat_id = str(random.randint(1000000, 9999999))
        self.test_message = f"Integration test message: {uuid.uuid4()}"

    def test_telegram_notification_flow(self):
        """
        Проверка реального взаимодействия с API Telegram.
        Ожидается получение ошибки от API (404), так как токен сгенерирован случайно.
        Важно: проверяем, что модуль корректно обрабатывает исключения и возвращает False,
        а не падает с ошибкой, согласно требованиям стабильности.
        """
        
        # Вызов функции модуля
        result = start_new(
            token=self.test_token,
            chat_id=self.test_chat_id,
            message=self.test_message
        )

        # Проверка: метод должен вернуть False при невалидном токене, не выбрасывая исключение наружу
        self.assertIsInstance(result, bool, "Функция должна возвращать булево значение")
        self.assertFalse(result, "При использовании случайного токена API должно вернуть ошибку (False)")

    def test_invalid_input_handling(self):
        """
        Проверка устойчивости к некорректным входным данным.
        """
        bad_inputs = [
            ("", "123", "msg"),
            ("token", "", "msg"),
            ("token", "123", ""),
            (None, None, None)
        ]

        for token, chat_id, msg in bad_inputs:
            with self.subTest(token=token, chat_id=chat_id, msg=msg):
                result = start_new(token, chat_id, msg)
                self.assertFalse(result, "Функция должна возвращать False при передаче пустых или некорректных данных")

if __name__ == '__main__':
    unittest.main()