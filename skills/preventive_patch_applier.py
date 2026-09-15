from skills.incident_trend_forecaster import IncidentTrendForecaster
from skills.error_recovery_hub import ErrorRecoveryHub


class PreventivePatchApplier:

    def __init__(self, forecaster=None, recovery_hub=None):
        self.forecaster = forecaster if forecaster is not None else IncidentTrendForecaster()
        self.recovery_hub = recovery_hub if recovery_hub is not None else ErrorRecoveryHub()

    def prevent_failures(self, module_name: str) -> dict:
        try:
            forecast = self.forecaster.forecast_future_incidents(module_name)
            incident_id = forecast.get("predicted_incident_id") if isinstance(forecast, dict) else None

            if not incident_id:
                return {
                    "success": False,
                    "incident_id": None,
                    "module_name": module_name
                }

            patch_data = self.recovery_hub.generate_patch(incident_id)
            self.recovery_hub.apply_patch(patch_data)

            return {
                "success": True,
                "incident_id": incident_id,
                "patch_data": patch_data,
                "module_name": module_name,
                "status": "success"
            }
        except Exception as e:
            return {
                "success": False,
                "incident_id": None,
                "error": str(e),
                "module_name": module_name
            }

    def prevent_failures_from_stream(self, module_name: str, stream) -> dict:
        try:
            forecast = self.forecaster.process_stream_and_forecast(module_name, stream)
            incident_id = forecast.get("predicted_incident_id") if isinstance(forecast, dict) else None

            if not incident_id:
                return {
                    "success": False,
                    "incident_id": None,
                    "module_name": module_name
                }

            patch_data = self.recovery_hub.generate_patch(incident_id)
            self.recovery_hub.apply_patch(patch_data)

            return {
                "success": True,
                "incident_id": incident_id,
                "patch_data": patch_data,
                "module_name": module_name,
                "status": "success"
            }
        except Exception as e:
            return {
                "success": False,
                "incident_id": None,
                "error": str(e),
                "module_name": module_name
            }

    def apply_preventive_patches(self, module_name: str) -> dict:
        res = self.prevent_failures(module_name)
        res["module_name"] = module_name
        if "success" in res and res["success"]:
            res["status"] = "success"
        else:
            res["status"] = "no_action_needed"
        return res

    def run_preventive_cycle(self, module_name: str) -> dict:
        return self.apply_preventive_patches(module_name)

    def process_module(self, module_name: str) -> dict:
        return self.apply_preventive_patches(module_name)

    def apply_patch_preventively(self, module_name: str) -> dict:
        return self.apply_preventive_patches(module_name)