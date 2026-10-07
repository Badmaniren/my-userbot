import datetime
import json
import statistics

class MarketStressRiskAggregator:
    def __init__(self, monte_carlo_engine=None, scenario_evaluator=None):
        self.monte_carlo_engine = monte_carlo_engine
        self.scenario_evaluator = scenario_evaluator

    def aggregate(self, portfolio_id, mc_data=None, matrix_data=None):
        if mc_data:
            var_val = mc_data.get("var_result", mc_data.get("var_95", 0.0))
        elif self.monte_carlo_engine:
            var_val = self.monte_carlo_engine.calculate_var(portfolio_id)
        else:
            var_val = 0.0

        if matrix_data:
            impact = matrix_data.get("scenario_impact", matrix_data.get("impact", 0.0))
        elif self.scenario_evaluator:
            eval_res = self.scenario_evaluator.evaluate(portfolio_id)
            impact = eval_res.get("impact", eval_res.get("scenario_impact", 0.0))
        else:
            impact = 0.0

        return {
            "portfolio_id": portfolio_id,
            "var_value": var_val,
            "scenario_impact": impact,
            "risk_score": float(var_val + abs(impact)),
            "timestamp": datetime.datetime.now().timestamp()
        }

    def _normalize(self, data):
        if not data:
            return 0.0
        return sum(data) / len(data)

    def normalize_risk_metrics(self, raw_data):
        return self._normalize(raw_data)

    def export_stress_report(self, filename, content=None):
        if content is None:
            content = "Stress Report Data"
        with open(filename, 'w') as f:
            try:
                f.write(content)
            except TypeError:
                if isinstance(content, str):
                    f.write(content.encode('utf-8'))
                else:
                    f.write(content)

    def check_critical_stress(self, threshold):
        current_risk = self.monte_carlo_engine.get_current_risk()
        return current_risk > threshold


def market_portfolio_stress_risk_aggregator(payload=None, **kwargs):
    if isinstance(payload, dict):
        pid = payload.get("portfolio_id")
        mc_data = payload.get("mc_data")
        matrix_data = payload.get("matrix_data")
    else:
        pid = kwargs.get("portfolio_id")
        mc_data = kwargs.get("mc_data")
        matrix_data = kwargs.get("matrix_data")

    aggregator = MarketStressRiskAggregator()
    return aggregator.aggregate(portfolio_id=pid, mc_data=mc_data, matrix_data=matrix_data)
