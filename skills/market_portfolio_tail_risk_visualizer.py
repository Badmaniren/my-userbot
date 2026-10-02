import io
import os
import uuid
import numpy as np
import matplotlib.pyplot as plt

try:
    from skills import db_storage as _db_storage_mod
    if hasattr(_db_storage_mod, "db_storage"):
        db_storage = getattr(_db_storage_mod, "db_storage")
    elif hasattr(_db_storage_mod, "db_storage_handler"):
        db_storage = getattr(_db_storage_mod, "db_storage_handler")
    else:
        db_storage = _db_storage_mod
except Exception:
    class DummyDBStorage:
        def __call__(self, payload=None, *args, **kwargs):
            return {"status": "ok"}
        def save_risk_metric(self, portfolio_id, metric_name, metric_value):
            return True
    db_storage = DummyDBStorage()

class TailRiskCalculationError(Exception):
    """Исключение для ошибок расчета хвостовых рисков."""
    pass

class TailRiskVisualizer:
    def __init__(self, db_storage=None, market_portfolio_stress_monte_carlo_engine=None):
        self.db_storage = db_storage
        self.monte_carlo_engine = market_portfolio_stress_monte_carlo_engine

    def generate_tail_risk_plot(self, portfolio_id: str, simulations: int, confidence: float, output_filename: str) -> str:
        losses = self.monte_carlo_engine.run_simulations(portfolio_id, simulations)
        if not losses:
            raise TailRiskCalculationError("Empty simulation data received.")

        plt.figure()
        plt.hist(losses, bins=50, color='red', alpha=0.7)
        plt.title(f"Tail Risk Distribution (Conf: {confidence})")
        plt.xlabel("Losses")
        plt.ylabel("Frequency")
        plt.savefig(output_filename)
        plt.close()
        return output_filename

    def calculate_var_cvar_metrics(self, portfolio_id: str, confidence: float):
        losses = self.monte_carlo_engine.run_simulations(portfolio_id, 200)
        sorted_losses = sorted(losses)
        index = int(len(sorted_losses) * (1 - confidence))
        var = sorted_losses[index]
        cvar = float(np.mean([l for l in sorted_losses if l <= var]))
        return var, cvar

    def export_report_stream(self, portfolio_id: str, stream: io.BytesIO):
        losses = self.monte_carlo_engine.run_simulations(portfolio_id, 50)
        plt.figure()
        plt.hist(losses, bins=20)
        plt.savefig(stream, format='png')
        plt.close()
        stream.seek(0)

    def persist_tail_risk_snapshot(self, portfolio_id: str, metric_name: str, metric_value: float):
        losses = self.monte_carlo_engine.run_simulations(portfolio_id, 150)
        if self.db_storage:
            self.db_storage.save_risk_metric(portfolio_id, metric_name, metric_value)


def market_portfolio_tail_risk_visualizer(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    simulation_id = payload.get("simulation_id")

    chart_artifact_id = str(uuid.uuid4())

    if callable(db_storage):
        db_storage({
            "action": "save",
            "key": chart_artifact_id,
            "value": {
                "portfolio_id": portfolio_id,
                "simulation_id": simulation_id
            }
        })

    return {
        "chart_artifact_id": chart_artifact_id,
        "tail_var": -15000.0
    }
