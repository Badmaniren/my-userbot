import io
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.preventive_patch_applier import PreventivePatchApplier


class TestPreventivePatchApplier(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex}"
        self.incident_id = f"incident_{uuid.uuid4().hex}"
        self.patch_data = {
            f"patch_key_{uuid.uuid4().hex}": f"patch_val_{uuid.uuid4().hex}"
        }
        self.stream_data = bytes(uuid.uuid4().hex, "utf-8")

    def test_prevent_failures_successful_flow(self):
        """Проверка полного успешного цикла превентивного наложения патча."""
        with patch(
            "skills.preventive_patch_applier.IncidentTrendForecaster"
        ) as mock_forecaster_cls, patch(
            "skills.preventive_patch_applier.ErrorRecoveryHub"
        ) as mock_hub_cls:

            mock_forecaster = mock_forecaster_cls.return_value
            mock_hub = mock_hub_cls.return_value

            mock_forecaster.forecast_future_incidents.return_value = {
                "predicted_incident_id": self.incident_id,
                "risk_level": "high",
                "confidence": random.uniform(0.8, 1.0),
            }

            mock_hub.generate_patch.return_value = self.patch_data
            mock_hub.apply_patch.return_value = {"status": "applied_successfully"}

            applier = PreventivePatchApplier()
            result = applier.prevent_failures(self.module_name)

            mock_forecaster.forecast_future_incidents.assert_called_once_with(
                self.module_name
            )
            mock_hub.generate_patch.assert_called_once_with(self.incident_id)
            mock_hub.apply_patch.assert_called_once_with(self.patch_data)

            self.assertTrue(result["success"])
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["patch_data"], self.patch_data)

    def test_prevent_failures_no_incident_predicted(self):
        """Проверка того, что патч не накладывается, если инцидент не прогнозируется."""
        with patch(
            "skills.preventive_patch_applier.IncidentTrendForecaster"
        ) as mock_forecaster_cls, patch(
            "skills.preventive_patch_applier.ErrorRecoveryHub"
        ) as mock_hub_cls:

            mock_forecaster = mock_forecaster_cls.return_value
            mock_hub = mock_hub_cls.return_value

            mock_forecaster.forecast_future_incidents.return_value = {
                "predicted_incident_id": None,
                "risk_level": "low",
                "confidence": random.uniform(0.0, 0.3),
            }

            applier = PreventivePatchApplier()
            result = applier.prevent_failures(self.module_name)

            mock_forecaster.forecast_future_incidents.assert_called_once_with(
                self.module_name
            )
            mock_hub.generate_patch.assert_not_called()
            mock_hub.apply_patch.assert_not_called()

            self.assertFalse(result["success"])
            self.assertIsNone(result["incident_id"])

    def test_prevent_failures_forecast_exception_handling(self):
        """Проверка корректной обработки исключений на этапе прогнозирования."""
        with patch(
            "skills.preventive_patch_applier.IncidentTrendForecaster"
        ) as mock_forecaster_cls, patch(
            "skills.preventive_patch_applier.ErrorRecoveryHub"
        ) as mock_hub_cls:

            mock_forecaster = mock_forecaster_cls.return_value
            mock_hub = mock_hub_cls.return_value

            error_message = f"Forecasting failed: {uuid.uuid4().hex}"
            mock_forecaster.forecast_future_incidents.side_effect = Exception(
                error_message
            )

            applier = PreventivePatchApplier()
            result = applier.prevent_failures(self.module_name)

            mock_forecaster.forecast_future_incidents.assert_called_once_with(
                self.module_name
            )
            mock_hub.generate_patch.assert_not_called()

            self.assertFalse(result["success"])
            self.assertIn(error_message, result["error"])

    def test_preventive_pipeline_with_stream(self):
        """Проверка превентивного пайплайна, работающего через анализ потока данных."""
        with patch(
            "skills.preventive_patch_applier.IncidentTrendForecaster"
        ) as mock_forecaster_cls, patch(
            "skills.preventive_patch_applier.ErrorRecoveryHub"
        ) as mock_hub_cls:

            mock_forecaster = mock_forecaster_cls.return_value
            mock_hub = mock_hub_cls.return_value

            mock_forecaster.process_stream_and_forecast.return_value = {
                "predicted_incident_id": self.incident_id,
                "risk_level": "critical",
            }
            mock_hub.generate_patch.return_value = self.patch_data
            mock_hub.apply_patch.return_value = {"status": "applied"}

            applier = PreventivePatchApplier()

            stream_mock = io.BytesIO(self.stream_data)
            result = applier.prevent_failures_from_stream(
                self.module_name, stream_mock
            )

            mock_forecaster.process_stream_and_forecast.assert_called_once()
            called_args = (
                mock_forecaster.process_stream_and_forecast.call_args[0]
            )
            self.assertEqual(called_args[0], self.module_name)
            self.assertIsInstance(called_args[1], io.BytesIO)

            mock_hub.generate_patch.assert_called_once_with(self.incident_id)
            mock_hub.apply_patch.assert_called_once_with(self.patch_data)

            self.assertTrue(result["success"])

    def test_prevent_failures_patch_application_error(self):
        """Проверка обработки ошибок при генерации или применении патча."""
        with patch(
            "skills.preventive_patch_applier.IncidentTrendForecaster"
        ) as mock_forecaster_cls, patch(
            "skills.preventive_patch_applier.ErrorRecoveryHub"
        ) as mock_hub_cls:

            mock_forecaster = mock_forecaster_cls.return_value
            mock_hub = mock_hub_cls.return_value

            mock_forecaster.forecast_future_incidents.return_value = {
                "predicted_incident_id": self.incident_id,
                "risk_level": "high",
            }

            patch_error = f"Patch generation failed: {uuid.uuid4().hex}"
            mock_hub.generate_patch.side_effect = Exception(patch_error)

            applier = PreventivePatchApplier()
            result = applier.prevent_failures(self.module_name)

            mock_hub.generate_patch.assert_called_once_with(self.incident_id)
            mock_hub.apply_patch.assert_not_called()

            self.assertFalse(result["success"])
            self.assertIn(patch_error, result["error"])


if __name__ == "__main__":
    unittest.main()