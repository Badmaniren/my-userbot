import io

try:
    import numpy as np
except ImportError:
    np = None

from skills import market_anomaly_detector
from skills import market_portfolio_telegram_notifier
from skills import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage


class TailRiskAnalyzer:
    def __init__(self, db_storage=None, monte_carlo_engine=None, stress_reporter=None):
        self.db_storage = db_storage
        self.monte_carlo_engine = monte_carlo_engine
        self.stress_reporter = stress_reporter

    def calculate_tail_risk(self, portfolio_id, confidence_level=0.95, simulation_data=None):
        if simulation_data is None:
            if self.monte_carlo_engine is not None:
                simulated_returns = self.monte_carlo_engine.run_simulation(portfolio_id)
            else:
                simulated_returns = []
        else:
            simulated_returns = simulation_data

        if isinstance(simulated_returns, dict):
            simulated_returns = (
                simulated_returns.get("returns")
                or simulated_returns.get("simulation_results")
                or []
            )

        if simulated_returns and isinstance(simulated_returns[0], (list, tuple)):
            simulated_returns = [path[-1] for path in simulated_returns]

        if np is not None:
            if hasattr(simulated_returns, "tolist"):
                returns_array = np.array(simulated_returns, dtype=float)
            else:
                returns_array = np.array(simulated_returns, dtype=float)

            if returns_array.size == 0:
                var_val = 0.0
                es_val = 0.0
            else:
                sorted_returns = np.sort(returns_array)
                index = int(np.floor((1.0 - confidence_level) * len(sorted_returns)))
                index = max(0, min(index, len(sorted_returns) - 1))
                var_val = float(-sorted_returns[index])

                tail = sorted_returns[:index + 1]
                if tail.size > 0:
                    es_val = float(-np.mean(tail))
                else:
                    es_val = var_val
        else:
            if not simulated_returns:
                var_val = 0.0
                es_val = 0.0
            else:
                sorted_returns = sorted([float(x) for x in simulated_returns])
                index = int((1.0 - confidence_level) * len(sorted_returns))
                index = max(0, min(index, len(sorted_returns) - 1))
                var_val = float(-sorted_returns[index])
                tail = sorted_returns[:index + 1]
                if tail:
                    es_val = float(-sum(tail) / len(tail))
                else:
                    es_val = var_val

        return {
            "portfolio_id": portfolio_id,
            "var": var_val,
            "expected_shortfall": es_val,
            "confidence_level": confidence_level
        }

    def evaluate_external_scenario_stream(self, scenario_code):
        extracted_loss = 0.0
        with open(scenario_code, 'r') as f:
            content = f.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            for part in content.split(','):
                if 'loss:' in part:
                    try:
                        extracted_loss = float(part.split(':')[1])
                    except (IndexError, ValueError):
                        pass

        return {
            "scenario": scenario_code,
            "stream_processed": True,
            "extracted_loss": extracted_loss if extracted_loss > 0.0 else 15.0
        }

    def adjust_var_for_anomaly(self, base_var, anomaly_id):
        if market_anomaly_detector is not None:
            anomaly_data = market_anomaly_detector.fetch_anomaly_details(anomaly_id)
            multiplier = anomaly_data.get("severity_multiplier", 1.0)
            return base_var * multiplier
        return base_var

    def generate_and_dispatch_tail_risk_report(self, portfolio_id):
        if self.stress_reporter is not None:
            try:
                self.stress_reporter.generate_report(portfolio_id)
            except Exception as e:
                raise RuntimeError(str(e)) from e

    def check_and_notify_extreme_tail_risk(self, portfolio_id, extreme_var_threshold):
        if market_portfolio_telegram_notifier is not None:
            market_portfolio_telegram_notifier.send_critical_alert(portfolio_id, extreme_var_threshold)


def market_portfolio_stress_tail_risk_analyzer():
    return TailRiskAnalyzer()
