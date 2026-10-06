import io
import uuid
import datetime

from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline
from skills.db_storage import db_storage


class MarketPortfolioStressHedgeExecutor:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage', db_storage)
        self.market_portfolio_stress_monte_carlo_engine = kwargs.get(
            'market_portfolio_stress_monte_carlo_engine', market_portfolio_stress_monte_carlo_engine
        )
        self.market_portfolio_scenario_simulator = kwargs.get(
            'market_portfolio_scenario_simulator', market_portfolio_scenario_simulator
        )
        self.market_portfolio_api_gateway = kwargs.get('market_portfolio_api_gateway')

    def execute_stress_hedges(self, portfolio_id):
        mc_result = self.market_portfolio_stress_monte_carlo_engine.simulate(portfolio_id)
        scenario_result = self.market_portfolio_scenario_simulator.evaluate(portfolio_id)

        asset = scenario_result.get('hedge_asset')
        volume = scenario_result.get('suggested_volume')

        order_response = self.market_portfolio_api_gateway.place_order({
            'portfolio_id': portfolio_id,
            'asset': asset,
            'volume': volume
        })

        return {
            'portfolio_id': portfolio_id,
            'asset': asset,
            'volume': volume,
            'order_status': order_response.get('status'),
            'executed_price': order_response.get('executed_price')
        }

    def log_audit_stream(self, stream):
        data = stream.read()
        log_id = self.db_storage.save_audit_log(data)
        return log_id


def market_portfolio_stress_hedge_executor(payload):
    execution_id = uuid.uuid4().hex
    if isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id")
    else:
        portfolio_id = str(payload)

    record = {
        "id": execution_id,
        "portfolio_id": portfolio_id,
        "status": "executed",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    db_storage({
        "action": "save",
        "table": "hedge_executions",
        "id": execution_id,
        "data": record
    })

    return {
        "execution_id": execution_id,
        "status": "success",
        "portfolio_id": portfolio_id
    }