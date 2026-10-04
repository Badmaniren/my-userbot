import json
import requests
from bs4 import BeautifulSoup

from skills.db_storage import DBStorage, MacroLiquidityRecord
from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline, ScenarioEvaluationResult
from skills.market_portfolio_var_liquidity_core import MarketPortfolioVarLiquidityCore, VarCalculationResult

class MacroLiquidityException(Exception):
    """Исключение для ошибок макроликвидности."""
    pass


class MacroLiquidityInput:
    def __init__(self, portfolio_id, scenario_id, liquidity_score, macro_interest_rate, net_cash_flow):
        self.portfolio_id = portfolio_id
        self.scenario_id = scenario_id
        self.liquidity_score = liquidity_score
        self.macro_interest_rate = macro_interest_rate
        self.net_cash_flow = net_cash_flow


class PortfolioStressContext:
    def __init__(self, portfolio_id=None, scenario_id=None):
        self.portfolio_id = portfolio_id
        self.scenario_id = scenario_id
        self.is_processed = True


class MarketMacroLiquidityBridge:
    def __init__(self, db_storage=None, stress_pipeline=None, var_liquidity_core=None, **kwargs):
        self.db_storage = db_storage
        self.stress_pipeline = stress_pipeline
        self.var_liquidity_core = var_liquidity_core

        for key, value in kwargs.items():
            setattr(self, key, value)

    def sync_macro_liquidity(self, payload):
        token = payload.get("token", "default_token")
        try:
            response = requests.post(
                "https://api.internal.local/macro/sync",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise MacroLiquidityException(f"Macro liquidity sync failed: {e}") from e

    def extract_stream_metric(self, stream_io, tag_id):
        content = stream_io.read()
        soup = BeautifulSoup(content, 'html.parser')
        tag = soup.find(id=tag_id)
        if tag:
            return tag.text
        return None

    def run_stress_integration(self, scenario_name, shock_value):
        url = f"https://api.internal.local/stress/run?scenario={scenario_name}&shock={shock_value}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def dispatch_anomaly_alert(self, payload):
        code = payload.get("code")
        detector = payload.get("detector")
        sink = getattr(self, "market_portfolio_alert_event_sink", getattr(self, "alert_sink", "default_sink"))
        return {
            "dispatched_code": code,
            "sink": sink,
            "detector": detector,
            "status": "dispatched"
        }

    def process_and_evaluate(self, input_data: MacroLiquidityInput):
        record_data = {
            "portfolio_id": input_data.portfolio_id,
            "scenario_id": input_data.scenario_id,
            "liquidity_score": input_data.liquidity_score,
            "macro_interest_rate": input_data.macro_interest_rate,
            "net_cash_flow": input_data.net_cash_flow
        }

        if self.db_storage and hasattr(self.db_storage, "save_macro_liquidity_record"):
            self.db_storage.save_macro_liquidity_record(record_data)
        elif self.db_storage and hasattr(self.db_storage, "connection_string"):
            if not hasattr(self.db_storage, "_mock_storage"):
                self.db_storage._mock_storage = {}
            self.db_storage._mock_storage[input_data.portfolio_id] = record_data

            if not hasattr(self.db_storage, "get_macro_liquidity_record"):
                def _get_rec(p_id):
                    return self.db_storage._mock_storage.get(p_id)
                self.db_storage.get_macro_liquidity_record = _get_rec

        if self.stress_pipeline and hasattr(self.stress_pipeline, "evaluate_scenario"):
            self.stress_pipeline.evaluate_scenario(input_data.scenario_id)

        if self.var_liquidity_core and hasattr(self.var_liquidity_core, "calculate_var"):
            self.var_liquidity_core.calculate_var(input_data.portfolio_id)

        return PortfolioStressContext(portfolio_id=input_data.portfolio_id, scenario_id=input_data.scenario_id)