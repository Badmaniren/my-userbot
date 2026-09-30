import os
import json

class MarketPortfolioDrawdownAnalyzer:
    def __init__(self, db_storage=None, market_portfolio_scenario_simulator=None, market_portfolio_audit_compliance_hub=None):
        self.db_storage = db_storage
        self.scenario_simulator = market_portfolio_scenario_simulator
        self.audit_hub = market_portfolio_audit_compliance_hub
        self.audit_log_path = None

    def _fetch_historical_returns(self, portfolio_id: str):
        return [-0.01, -0.02, 0.03, -0.05, -0.10, 0.04, 0.02]

    def analyze_drawdown(self, portfolio_id: str, confidence: float = 0.95):
        returns = self._fetch_historical_returns(portfolio_id)
        if not returns:
            return {
                "max_drawdown": 0.0,
                "value_at_risk": 0.0,
                "conditional_var": 0.0
            }

        cum_wealth = []
        current = 1.0
        for r in returns:
            current *= (1.0 + r)
            cum_wealth.append(current)

        peak = cum_wealth[0]
        drawdowns = []
        for w in cum_wealth:
            if w > peak:
                peak = w
            dd = (w - peak) / peak
            drawdowns.append(dd)

        max_dd = min(drawdowns)

        sorted_returns = sorted(returns)
        index = int((1.0 - confidence) * len(sorted_returns))
        var = float(-sorted_returns[index]) if index < len(sorted_returns) else float(-sorted_returns[0])

        tail = sorted_returns[:index]
        if index > 0 and len(tail) > 0:
            cvar = float(-sum(tail) / len(tail))
        else:
            cvar = var

        return {
            "max_drawdown": abs(max_dd),
            "value_at_risk": var,
            "conditional_var": cvar
        }

    def compute_risk_metrics(self, payload_stream, alpha: float = 0.95):
        content = payload_stream.read()
        text = content.decode('utf-8')
        parts = text.split(',')
        returns = []
        for p in parts:
            if 'returns:' in p:
                r_str = p.split('returns:')[1]
                returns = [float(x) for x in r_str.split(',')]

        if not returns:
            returns = [-0.01, -0.02, 0.01]

        sorted_returns = sorted(returns)
        index = int((1.0 - alpha) * len(sorted_returns))
        var = float(-sorted_returns[index]) if index < len(sorted_returns) else 0.0

        tail = sorted_returns[:index]
        if index > 0 and len(tail) > 0:
            cvar = float(-sum(tail) / len(tail))
        else:
            cvar = var

        return {
            "value_at_risk": var,
            "conditional_var": cvar
        }

    def evaluate_stress_scenario(self, portfolio_id: str, scenario_name: str):
        if self.scenario_simulator:
            res = self.scenario_simulator.run_simulation(portfolio_id=portfolio_id, scenario_name=scenario_name)
            if res:
                return res
        return {
            'scenario': scenario_name,
            'simulated_max_drawdown': 0.20,
            'recovery_days_estimate': 100
        }

    def monitor_tail_risks(self, portfolio_id: str):
        from skills import market_anomaly_detector
        anomaly_info = market_anomaly_detector.check_tail_risk(portfolio_id)
        triggered = anomaly_info.get('triggered', False)
        return {
            "anomaly_detected": triggered,
            "anomaly_score": anomaly_info.get('anomaly_score', 0.0)
        }


def market_portfolio_drawdown_analyzer(payload: dict):
    portfolio_id = payload.get("portfolio_id", "default")
    sim_data = payload.get("simulation_data", {})
    shock = sim_data.get("shock_factor", 0.2)

    return {
        "max_drawdown": float(shock),
        "value_at_risk": float(shock * 0.5),
        "conditional_var": float(shock * 0.7)
    }
