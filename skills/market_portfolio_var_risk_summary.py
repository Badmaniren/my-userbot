import json


class MarketPortfolioVaRRiskSummary:
    """Легковесный модуль для агрегации метрик Value at Risk (VaR) и формирования итоговой сводки по портфельным рискам."""

    def __init__(self, portfolio_id, var_metric, risk_level):
        self.portfolio_id = portfolio_id
        self.var_metric = var_metric
        self.risk_level = risk_level

    def generate_summary(self):
        if not self.portfolio_id:
            raise ValueError("Invalid portfolio ID")
        return {
            "portfolio_id": self.portfolio_id,
            "var_metric": self.var_metric,
            "risk_level": self.risk_level,
            "status": "aggregated"
        }


def summarize_portfolio_var_risk(portfolio_id, confidence, monte_carlo_metrics):
    """Интеграционная функция для расчета и сохранения итоговой сводки по рискам портфеля."""
    total_var = float(monte_carlo_metrics.get("var_estimate", 0.0))

    summary_result = {
        "portfolio_id": portfolio_id,
        "confidence_level": confidence,
        "total_var": total_var,
        "status": "aggregated"
    }

    summary_file_path = f"var_summary_{portfolio_id}.json"
    with open(summary_file_path, "w", encoding="utf-8") as f:
        json.dump(summary_result, f, ensure_ascii=False, indent=4)

    return summary_result
