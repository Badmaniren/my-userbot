import sys
import os
import gc
import time
import functools
import tracemalloc

class MemoryLimitExceeded(Exception):
    """Вызывается, когда потребление памяти превышает допустимый лимит бесплатного тарифа."""
    pass

def force_gc():
    """Принудительный запуск сборщика мусора."""
    gc.collect()

def get_current_memory():
    """Возвращает текущее потребление памяти в МБ."""
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def assert_memory_limit(max_mb: float):
    """Проверяет текущее потребление памяти относительно лимита."""
    if max_mb <= 0:
        raise ValueError("Лимит памяти должен быть положительным числом.")
    current_mb = get_current_memory()
    if current_mb > max_mb:
        raise MemoryLimitExceeded(f"Превышен лимит памяти: {current_mb:.2f} МБ > {max_mb} МБ")
    return current_mb

def profile_memory(func=None, *, max_mb=None):
    """Декоратор для профилирования памяти функции."""
    if func is None:
        return lambda f: profile_memory(f, max_mb=max_mb)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
            if max_mb is not None:
                assert_memory_limit(max_mb)
            return result
        finally:
            if not was_tracing:
                tracemalloc.stop()
            force_gc()

    return wrapper

profile = profile_memory

def track_resources(target):
    """Отслеживает ресурсы для переданного объекта. Вызывает исключение при некорректном вводе."""
    if not callable(target):
        raise TypeError("Цель для отслеживания ресурсов должна быть вызываемой (callable).")
    return target()

def profile_with_timeout(func, timeout: float):
    """Профилирование функции с симуляцией таймаута."""
    if timeout <= 0:
        raise ValueError("Таймаут должен быть больше нуля.")
    start_time = time.time()
    res = func()
    duration = time.time() - start_time
    if duration > timeout:
        raise TimeoutError("Превышено время выполнения задачи.")
    return res

class MemoryProfiler:
    """Класс для замеров потребления памяти в контексте."""
    def __init__(self):
        self._started = False

    def start(self):
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        self._started = True

    def stop(self):
        current, peak = tracemalloc.get_traced_memory()
        if self._started and not tracemalloc.is_tracing():
            pass
        return {"current": current, "peak": peak}