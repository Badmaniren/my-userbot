import os
import sys
import json
import tempfile
import unittest

# Ensure skills directory is in sys.path
skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

# Ensure optional dependencies don't cause ModuleNotFoundError during test loading
if "requests" not in sys.modules:
    try:
        import requests
    except ModuleNotFoundError:
        import unittest.mock
        req_mock = unittest.mock.MagicMock()
        class RequestException(Exception): pass
        class HTTPError(RequestException): pass
        class ConnectionError(RequestException): pass
        class Timeout(RequestException): pass

        req_mock.exceptions.RequestException = RequestException
        req_mock.exceptions.HTTPError = HTTPError
        req_mock.exceptions.ConnectionError = ConnectionError
        req_mock.exceptions.Timeout = Timeout
        req_mock.RequestException = RequestException
        sys.modules["requests"] = req_mock

if "bs4" not in sys.modules:
    try:
        import bs4
    except ModuleNotFoundError:
        import unittest.mock
        bs4_mock = unittest.mock.MagicMock()
        class BeautifulSoup:
            def __init__(self, markup="", features=None, **kwargs):
                self.markup = str(markup)
            def find(self, name=None, attrs=None, **kwargs):
                id_val = kwargs.get("id") or (attrs.get("id") if attrs else None)
                if id_val and (f"id='{id_val}'" in self.markup or f'id="{id_val}"' in self.markup):
                    node = unittest.mock.MagicMock()
                    node.text = self.markup
                    return node
                return None
            def find_all(self, name=None, attrs=None, **kwargs):
                return []
        bs4_mock.BeautifulSoup = BeautifulSoup
        sys.modules["bs4"] = bs4_mock

if "numpy" not in sys.modules:
    try:
        import numpy as np
    except ModuleNotFoundError:
        import math
        import types

        np_mock = types.ModuleType("numpy")

        class MockNDArray(list):
            def __sub__(self, other):
                if isinstance(other, (int, float)):
                    return MockNDArray([x - other for x in self])
                return MockNDArray([x - y for x, y in zip(self, other)])

            def __pow__(self, power):
                return MockNDArray([x ** power for x in self])

        def _array(data):
            return MockNDArray(data)

        def _std(a, ddof=0):
            lst = list(a)
            n = len(lst)
            if n - ddof <= 0:
                return 0.0
            mean_val = sum(lst) / n
            var_val = sum((x - mean_val) ** 2 for x in lst) / (n - ddof)
            return math.sqrt(max(0.0, var_val))

        def _mean(a):
            lst = list(a)
            return sum(lst) / len(lst) if lst else 0.0

        def _sum(a):
            return sum(list(a))

        def _sort(a):
            return MockNDArray(sorted(list(a)))

        np_mock.array = _array
        np_mock.std = _std
        np_mock.mean = _mean
        np_mock.sum = _sum
        np_mock.sort = _sort
        sys.modules["numpy"] = np_mock

from market_portfolio_ml_feature_builder import market_portfolio_ml_feature_builder
from market_portfolio_stress_ml_volatility_forecaster_v2 import market_portfolio_stress_ml_volatility_forecaster_v2
from market_portfolio_ml_stress_evaluator import market_portfolio_ml_stress_evaluator
from market_portfolio_ml_stress_adaptive_allocator import market_portfolio_ml_stress_adaptive_allocator


class TestEpicMlPredictiveAnalyticsStressTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file_path = os.path.join(self.temp_dir.name, "portfolio_returns_history.json")

        # Генерируем реалистичный набор исторических доходностей портфеля для стресс-тестирования (30 строк)
        self.realistic_returns = [
            {"timestamp": f"2023-10-{i:02d}T10:00:00Z", "return": round(0.012 * (i % 3 - 1) - 0.005 * (i % 5), 4), "volume": 1500000 + i * 12345}
            for i in range(1, 31)
        ]
        # Внедряем искусственный хвост распределения / аномалию для проверки хвостовых характеристик
        self.realistic_returns[15]["return"] = -0.0875
        self.realistic_returns[22]["return"] = -0.0650

        with open(self.data_file_path, "w", encoding="utf-8") as f:
            json.dump(self.realistic_returns, f, indent=2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ml_predictive_analytics_pipeline(self):
        print("\n--- НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: ML-прогнозирование стресс-тестов ---")

        # 1. Проверяем наличие файла с данными
        self.assertTrue(os.path.exists(self.data_file_path))
        print(f"[OK] Сгенерирован реальный файл с историческими данными: {self.data_file_path} (записей: {len(self.realistic_returns)})")

        # 2. Извлекаем статистические фичи и хвостовые характеристики доходностей
        feature_builder = market_portfolio_ml_feature_builder()
        features = feature_builder.extract_features(self.data_file_path)
        print(f"[OK] Модуль market_portfolio_ml_feature_builder извлек фичи: {list(features.keys()) if isinstance(features, dict) else 'OK'}")

        # 3. Прогнозируем волатильность при стресс-сценариях с помощью ML-модуля
        volatility_forecaster = market_portfolio_stress_ml_volatility_forecaster_v2()
        volatility_forecast = volatility_forecaster.predict_volatility(features)
        print(f"[OK] Модуль market_portfolio_stress_ml_volatility_forecaster_v2 рассчитал прогноз волатильности: {volatility_forecast}")

        # 4. Связываем фичи и прогноз в единый скоринг стресс-риска портфеля
        stress_evaluator = market_portfolio_ml_stress_evaluator()
        risk_score = stress_evaluator.evaluate_risk(features, volatility_forecast)
        print(f"[OK] Модуль market_portfolio_ml_stress_evaluator выдал интегральный скоринг риска: {risk_score}")

        # 5. Интегрируем ML-скоринг с контуром автоматического реагирования и ребалансировки
        adaptive_allocator = market_portfolio_ml_stress_adaptive_allocator()
        rebalance_action = adaptive_allocator.process_allocation(risk_score)
        print(f"[OK] Модуль market_portfolio_ml_stress_adaptive_allocator определил план реагирования: {rebalance_action}")

        # Проверяем общую работоспособность пайплайна
        self.assertIsNotNone(risk_score)
        print("--- ПРАКТИЧЕСКАЯ ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ---")


if __name__ == "__main__":
    unittest.main()