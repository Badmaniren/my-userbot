from skills import anomaly_forecaster
from skills import anomaly_reactor
from skills.anomaly_forecaster import AnomalyForecaster
from skills.anomaly_reactor import AutonomousReactorEngine


class AnomalyDefenseHub:
    def __init__(self, log_path=None, model_name=None, threshold=None, forecaster=None, reactor=None):
        if forecaster is not None:
            self.forecaster = forecaster
        else:
            kwargs = {}
            if log_path is not None:
                kwargs["log_path"] = log_path
            if model_name is not None:
                kwargs["model_name"] = model_name
            if threshold is not None:
                kwargs["threshold"] = threshold
            self.forecaster = AnomalyForecaster(**kwargs)

        if reactor is not None:
            self.reactor = reactor
        else:
            self.reactor = AutonomousReactorEngine()

    def run_defense_cycle(self, telemetry_data):
        return self.process_telemetry(telemetry_data)

    def process_telemetry(self, telemetry_data):
        forecast = self.forecaster.predict(telemetry_data)

        reaction = None
        is_anomaly = getattr(forecast, "is_anomaly", False)

        if is_anomaly:
            if hasattr(self.reactor, "handle_anomaly"):
                reaction = self.reactor.handle_anomaly(forecast)

        if reaction is None:
            reaction = {"status": "ok"}

        return {
            "forecast": forecast,
            "reaction": reaction
        }

    def process_stream(self, stream):
        if hasattr(self.forecaster, "parse_raw_stream"):
            telemetry_data = self.forecaster.parse_raw_stream(stream)
            if telemetry_data:
                return self.process_telemetry(telemetry_data)
        return None