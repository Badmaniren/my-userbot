import uuid
import random
import io

from skills.market_portfolio_data_exporter import market_portfolio_data_exporter
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class MarketPortfolioDeepStressAnalyzer:
    def __init__(self, db_storage=None, market_portfolio_liquidity_scenario_analyzer=None, market_portfolio_scenario_simulator=None):
        self.db_storage = db_storage
        self.liquidity_analyzer = market_portfolio_liquidity_scenario_analyzer
        self.scenario_simulator = market_portfolio_scenario_simulator

    def run_deep_stress_analysis(self, portfolio_id: str, scenario_name: str, historical_window: int):
        analysis_id = str(uuid.uuid4())

        liquidity_metrics = {}
        if self.liquidity_analyzer and hasattr(self.liquidity_analyzer, 'get_historical_liquidity'):
            liquidity_metrics = self.liquidity_analyzer.get_historical_liquidity(
                portfolio_id=portfolio_id, window=historical_window
            )

        simulation_results = {}
        if self.scenario_simulator and hasattr(self.scenario_simulator, 'run_simulation'):
            simulation_results = self.scenario_simulator.run_simulation(
                scenario_name=scenario_name, window=historical_window
            )

        result = {
            'analysis_id': analysis_id,
            'portfolio_id': portfolio_id,
            'scenario_name': scenario_name,
            'liquidity_metrics': liquidity_metrics,
            'simulation_results': simulation_results
        }

        if self.db_storage and hasattr(self.db_storage, 'save_analysis'):
            self.db_storage.save_analysis(result)

        return result

    def run_deep_stress_analysis_and_export(self, portfolio_id: str, scenario_name: str, export_format: str):
        export_stream = market_portfolio_data_exporter.export(portfolio_id=portfolio_id, format=export_format)

        return {
            'format': export_format,
            'metadata': f"Exported portfolio {portfolio_id} for scenario {scenario_name}",
            'data': export_stream
        }

    def evaluate_historical_volatility_impact(self, asset_ticker: str, volatility_spike: float):
        cursor = self.db_storage.connection.cursor()
        rows = cursor.fetchall()

        total_val = 0.0
        for row in rows:
            total_val += row[1] * row[2]

        adjusted_var = total_val * volatility_spike * 0.1

        return {
            'ticker': asset_ticker,
            'adjusted_var': max(adjusted_var, 1.0)
        }

    def aggregate_stress_signals(self, signals_input: list):
        processed = []
        risk_score_sum = 0.0

        for sig in signals_input:
            severity = sig.get('severity', 'LOW')
            multiplier = 1.0
            if severity == 'MEDIUM':
                multiplier = 2.0
            elif severity == 'HIGH':
                multiplier = 3.0
            elif severity == 'CRITICAL':
                multiplier = 5.0

            processed.append({
                'id': sig['id'],
                'severity': severity
            })
            risk_score_sum += multiplier * 15.0

        return {
            'processed_signals': processed,
            'aggregate_risk_score': min(risk_score_sum, 100.0)
        }


def market_portfolio_deep_stress_analyzer(stress_input: dict):
    portfolio_id = stress_input.get("portfolio_id", "default_port")
    historical_drop = stress_input.get("historical_drop_pct", 20.0)
    liquidity_data = stress_input.get("liquidity_data", {})

    depth_score = liquidity_data.get("depth_score", 0.5)

    stress_score = float(historical_drop) * (1.0 + float(depth_score))
    max_drawdown = -float(historical_drop) / 100.0

    return {
        "portfolio_id": portfolio_id,
        "stress_score": round(stress_score, 2),
        "max_drawdown": round(max_drawdown, 4),
        "status": "completed"
    }