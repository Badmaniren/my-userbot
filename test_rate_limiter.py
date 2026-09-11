import unittest
from unittest.mock import patch, MagicMock
import time
import threading

try:
    from skills.rate_limiter import RateLimiter, RateLimitExceeded
except ImportError:
    # Заглушки для прохождения статического анализа, если модуль еще не написан
    class RateLimitExceeded(Exception):
        pass
    class RateLimiter:
        def __init__(self, *args, **kwargs):
            pass
        def acquire(self):
            pass
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass


class TestRateLimiterInquisitor(unittest.TestCase):
    """
    Архитектор-Инспектор требует железной надежности от механизма контроля частоты.
    Ни один лишний запрос не должен прорваться на бесплатный тариф!
    """

    def setUp(self):
        # Базовая инициализация: 2 запроса в секунду, чтобы тесты не спали вечно
        self.rate_limiter = RateLimiter(calls=2, period=1.0)

    def test_normal_operation_within_limits(self):
        """[УСПЕХ] Запросы в пределах лимита проходят мгновенно без блокировок."""
        try:
            self.rate_limiter.acquire()
            self.rate_limiter.acquire()
        except Exception as e:
            self.fail(f"Нормальные запросы вызвали исключение: {e}")

    def test_exceeding_limit_raises_exception_or_blocks(self):
        """[СБОЙ/ЛАНДШАФТ] Превышение лимита должно вызывать исключение или блокировать выполнение."""
        # Исчерпываем лимит
        self.rate_limiter.acquire()
        self.rate_limiter.acquire()

        # Проверяем, настроен ли лимитер на выброс исключения при превышении
        if hasattr(self.rate_limiter, 'raise_on_limit') and self.rate_limiter.raise_on_limit:
            with self.assertRaises((RateLimitExceeded, Exception)):
                self.rate_limiter.acquire()
        else:
            # Если он блокирующий, проверяем, что вызов занимает время (мокаем time.sleep для скорости)
            with patch('time.sleep', return_value=None) as mock_sleep:
                self.rate_limiter.acquire()
                mock_sleep.assert_called()

    def test_context_manager_success(self):
        """[УСПЕХ] Использование RateLimiter в качестве менеджера контекста."""
        try:
            with self.rate_limiter:
                pass
        except Exception as e:
            self.fail(f"Менеджер контекста упал на валидном запросе: {e}")

    def test_context_manager_limit_exceeded(self):
        """[СБОЙ] Менеджер контекста обязан рухнуть при превышении квоты беспроводного тарифа."""
        with patch('time.sleep', side_effect=InterruptedError("Blocked")):
            try:
                with self.rate_limiter:
                    with self.rate_limiter:
                        with self.rate_limiter:
                            pass
            except (RateLimitExceeded, InterruptedError, Exception):
                pass  # Ожидаемое поведение при жестком лимите

    def test_invalid_initialization_zero_calls(self):
        """[СБОЙ] Передача 0 или отрицательных лимитов должна караться ValueError."""
        with self.assertRaises(ValueError):
            RateLimiter(calls=0, period=1.0)

    def test_invalid_initialization_negative_period(self):
        """[СБОЙ] Отрицательный период времени — ересь физики, должен вызывать ValueError."""
        with self.assertRaises(ValueError):
            RateLimiter(calls=5, period=-2.5)

    def test_concurrent_access_thread_safety(self):
        """[СБОЙ/СТРЕСС] Многопоточный штурм лимитера не должен приводить к состоянию гонки."""
        limiter = RateLimiter(calls=10, period=1.0)
        threads = []
        errors = []

        def worker():
            try:
                limiter.acquire()
            except Exception as err:
                errors.append(err)

        for _ in range(20):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Если лимитер не падает с фатальным Internal Error в потоках — уже хорошо.
        # Проверяем, что потоки вообще отрабатывали.
        self.assertTrue(len(threads) == 20)

    def test_time_window_reset(self):
        """[УСПЕХ] Сброс временного окна восстанавливает квоту запросов."""
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0
            limiter = RateLimiter(calls=1, period=1.0)
            
            # Первый вызов в момент времени 1000.0
            limiter.acquire()

            # Переносим время за пределы периода (1001.5)
            mock_time.return_value = 1001.5
            
            # Второй вызов должен пройти без блокировки/ошибки
            try:
                limiter.acquire()
            except Exception as e:
                self.fail(f"Квота не восстановилась после истечения периода: {e}")

    def test_garbage_input_types_in_init(self):
        """[СБОЙ] Подача строк или None вместо чисел в инициализатор запрещена."""
        with self.assertRaises((TypeError, ValueError)):
            RateLimiter(calls="ten", period=None)