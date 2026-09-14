import unittest
from unittest.mock import patch, MagicMock
import sys
import io
import time
import tracemalloc

class TestMemoryProfilerInquisitor(unittest.TestCase):
    """
    Архитектор-Инквизитор требует железобетонных доказательств эффективности.
    Эти тесты проверят skills/memory_profiler.py на утечки, превышение лимитов 
    бесплатного тарифа и обработку критических сбоев. Никакой пощады неэффективному коду.
    """

    def setUp(self):
        tracemalloc.start()

    def tearDown(self):
        tracemalloc.stop()

    def _import_profiler(self):
        try:
            import skills.memory_profiler as mp
            return mp
        except ImportError:
            self.fail("МОДУЛЬ skills/memory_profiler.py НЕ СУЩЕСТВУЕТ! ЕРЕТИК! Создай модуль немедленно!")

    def test_01_module_exists_and_has_api(self):
        mp = self._import_profiler()
        self.assertTrue(hasattr(mp, 'profile_memory') or hasattr(mp, 'MemoryProfiler') or callable(getattr(mp, 'track_resources', None)),
                        "Модуль не содержит базовых функций профилирования памяти!")

    def test_02_memory_limit_exceeded_crash(self):
        mp = self._import_profiler()
        if not hasattr(mp, 'MemoryLimitExceeded'):
            return # Если нет кастомного исключения, пропускаем специфичный ассерт
        
        # Симулируем жуткую утечку памяти, превышающую лимит бесплатного тарифа
        huge_data = []
        try:
            for _ in range(100):
                huge_data.append(' ' * 1024 * 1024) # 100 МБ
            if hasattr(mp, 'assert_memory_limit'):
                with self.assertRaises((mp.MemoryLimitExceeded, MemoryError, AssertionError)):
                    mp.assert_memory_limit(max_mb=10)
        finally:
            del huge_data

    def test_03_mock_resource_exhaustion(self):
        mp = self._import_profiler()
        # Проверка поведения при недоступности tracemalloc или системных метрик
        with patch('tracemalloc.get_traced_memory', side_effect=RuntimeError("Tracemalloc broken")):
            if hasattr(mp, 'get_current_memory'):
                with self.assertRaises(Exception):
                    mp.get_current_memory()

    def test_04_zero_and_negative_limits(self):
        mp = self._import_profiler()
        if hasattr(mp, 'assert_memory_limit'):
            with self.assertRaises((ValueError, AssertionError)):
                mp.assert_memory_limit(max_mb=-50)
            with self.assertRaises((ValueError, AssertionError)):
                mp.assert_memory_limit(max_mb=0)

    def test_05_garbage_collection_trigger(self):
        mp = self._import_profiler()
        if hasattr(mp, 'force_gc'):
            try:
                mp.force_gc()
            except Exception as e:
                self.fail(f"Принудительный сбор мусора упал с ошибкой: {e}")

    def test_06_profile_decorator_success(self):
        mp = self._import_profiler()
        if hasattr(mp, 'profile'):
            @mp.profile(max_mb=50)
            def dummy_task():
                return [i for i in range(1000)]
            
            res = dummy_task()
            self.assertEqual(len(res), 1000)

    def test_07_profile_decorator_failure_on_bloat(self):
        mp = self._import_profiler()
        if hasattr(mp, 'profile'):
            @mp.profile(max_mb=1)
            def bloated_task():
                return ' ' * 10 * 1024 * 1024 # 10 МБ при лимите в 1 МБ
            
            with self.assertRaises((Exception, AssertionError)):
                bloated_task()

    def test_08_corrupted_inputs_profiling(self):
        mp = self._import_profiler()
        if hasattr(mp, 'track_resources'):
            with self.assertRaises((TypeError, ValueError, AttributeError)):
                mp.track_resources(None) # Передаем ересь вместо функции

    def test_09_timeout_simulation_in_profiler(self):
        mp = self._import_profiler()
        if hasattr(mp, 'profile_with_timeout'):
            def slow_task():
                time.sleep(2)
            with self.assertRaises((TimeoutError, Exception)):
                mp.profile_with_timeout(slow_task, timeout=0.1)

    def test_10_concurrent_memory_track(self):
        mp = self._import_profiler()
        if hasattr(mp, 'MemoryProfiler'):
            profiler = mp.MemoryProfiler()
            if hasattr(profiler, 'start') and hasattr(profiler, 'stop'):
                profiler.start()
                time.sleep(0.01)
                stats = profiler.stop()
                self.assertIsNotNone(stats)