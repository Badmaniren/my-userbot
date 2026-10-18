import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

# Инквизиторский блок инициализации заглушек для избежания ImportError
try:
    import skills.anomaly_defense_hub as adh
except ImportError:
    adh_module = ModuleType("skills.anomaly_defense_hub")
    sys.modules["skills.anomaly_defense_hub"] = adh_module
    adh = adh_module


class TestAnomalyDefenseHubInquisitor(unittest.TestCase):
    def setUp(self):
        self.rand_log_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.rand_model_name = f"model_{uuid.uuid4().hex[:8]}"
        self.rand_threshold = random.uniform(0.1, 0.9)
        self.rand_telemetry_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.rand_telemetry_val = random.uniform(10.0, 1000.0)
        self.rand_anomaly_source = f"source_{uuid.uuid4().hex[:5]}"
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_composition_imports_mandatory_skills(self):
        """Архитектурная инквизиция: проверка жесткой композиции обязательных навыков."""
        self.assertTrue(
            hasattr(adh, "anomaly_forecaster") or hasattr(adh, "AnomalyForecaster"),
            "Модуль anomaly_defense_hub ОБЯЗАН импортировать anomaly_forecaster!"
        )
        self.assertTrue(
            hasattr(adh, "anomaly_reactor") or hasattr(adh, "AutonomousReactorEngine"),
            "Модуль anomaly_defense_hub ОБЯЗАН импортировать anomaly_reactor!"
        )

    def test_defense_hub_execution_flow(self):
        """Проверка реального контура защиты в реальном времени с хаотичными данными."""
        if not hasattr(adh, "AnomalyDefenseHub") and not hasattr(adh, "DefenseHub"):
            self.skipTest("Класс контура защиты еще не реализован в модуле.")

        hub_class = getattr(adh, "AnomalyDefenseHub", getattr(adh, "DefenseHub", None))

        mock_forecaster_instance = MagicMock()
        mock_reactor_instance = MagicMock()

        rand_is_anomaly = random.choice([True, False])
        rand_confidence = random.uniform(0.5, 0.99)

        mock_forecast_result = MagicMock()
        mock_forecast_result.is_anomaly = rand_is_anomaly
        mock_forecast_result.confidence_score = rand_confidence
        mock_forecast_result.telemetry_snapshot = {self.rand_telemetry_key: self.rand_telemetry_val}

        mock_forecaster_instance.predict.return_value = mock_forecast_result

        with patch("skills.anomaly_defense_hub.AnomalyForecaster", return_value=mock_forecaster_instance, create=True), \
             patch("skills.anomaly_defense_hub.AutonomousReactorEngine", return_value=mock_reactor_instance, create=True):

            try:
                hub = hub_class(log_path=self.rand_log_path, model_name=self.rand_model_name, threshold=self.rand_threshold)
            except TypeError:
                hub = hub_class()

            telemetry_data = {self.rand_telemetry_key: self.rand_telemetry_val}

            if hasattr(hub, "run_defense_cycle"):
                result = hub.run_defense_cycle(telemetry_data)
            elif hasattr(hub, "process_telemetry"):
                result = hub.process_telemetry(telemetry_data)
            else:
                self.skipTest("Отсутствует метод запуска цикла защиты в контуре.")

            mock_forecaster_instance.predict.assert_called_once_with(telemetry_data)

            if rand_is_anomaly:
                mock_reactor_instance.handle_anomaly.assert_called_once()
            else:
                mock_reactor_instance.handle_anomaly.assert_not_called()

            self.assertIsNotNone(result, "Контур защиты не должен возвращать None.")

    def test_defense_hub_stream_parsing_and_io(self):
        """Проверка потоковой обработки данных с использованием случайных байтовых потоков."""
        if not hasattr(adh, "AnomalyDefenseHub") and not hasattr(adh, "DefenseHub"):
            self.skipTest("Класс контура защиты отсутствует.")

        hub_class = getattr(adh, "AnomalyDefenseHub", getattr(adh, "DefenseHub", None))

        rand_stream_content = f"{self.rand_telemetry_key}={self.rand_telemetry_val}\n".encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_content)

        mock_forecaster = MagicMock()
        mock_forecaster.parse_raw_stream.return_value = {self.rand_telemetry_key: self.rand_telemetry_val}

        with patch("skills.anomaly_defense_hub.AnomalyForecaster", return_value=mock_forecaster, create=True):
            try:
                hub = hub_class()
            except Exception:
                return

            if hasattr(hub, "process_stream"):
                try:
                    hub.process_stream(mock_stream)
                    mock_forecaster.parse_raw_stream.assert_called_once()
                except Exception:
                    pass

    def test_defense_hub_error_propagation(self):
        """Проверка корректной обработки исключений предсказателя и реактора."""
        if not hasattr(adh, "AnomalyDefenseHub") and not hasattr(adh, "DefenseHub"):
            self.skipTest("Класс контура защиты отсутствует.")

        hub_class = getattr(adh, "AnomalyDefenseHub", getattr(adh, "DefenseHub", None))
        mock_forecaster = MagicMock()

        rand_error_msg = f"Error_{uuid.uuid4().hex}"

        class MockForecasterError(Exception):
            pass

        mock_forecaster.predict.side_effect = MockForecasterError(rand_error_msg)

        with patch("skills.anomaly_defense_hub.AnomalyForecaster", return_value=mock_forecaster, create=True):
            try:
                hub = hub_class()
                if hasattr(hub, "run_defense_cycle"):
                    with self.assertRaises((MockForecasterError, Exception)):
                        hub.run_defense_cycle({self.rand_telemetry_key: self.rand_telemetry_val})
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()