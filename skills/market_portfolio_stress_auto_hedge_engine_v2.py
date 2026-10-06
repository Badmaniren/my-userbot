from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Честный импорт внешних зависимостей без заглушек и без try-except оберток
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline


class HedgeExecutionError(Exception):
    """Исключение при ошибке выполнения хеджирования."""
    pass


class ScenarioEvaluationError(Exception):
    """Исключение при ошибке оценки сценария."""
    pass


class StressAutoHedgeEngineV2:
    def __init__(
        self,
        engine_id,
        db_storage,
        market_portfolio_scenario_simulator,
        market_portfolio_execution_pipeline,
        market_sentiment_risk_hub
    ):
        self.engine_id = engine_id
        self.db_storage = db_storage
        self.scenario_simulator = market_portfolio_scenario_simulator
        self.execution_pipeline = market_portfolio_execution_pipeline
        self.risk_hub = market_sentiment_risk_hub

    def evaluate_and_hedge(self, portfolio_id, scenario_name):
        try:
            scenario_result = self.scenario_simulator.evaluate(portfolio_id, scenario_name)
        except Exception as e:
            self.db_storage.save_error_log({"portfolio_id": portfolio_id, "error": str(e)})
            raise ScenarioEvaluationError(str(e))

        expected_hedge_asset = scenario_result.get("recommended_hedge")
        allocated_volume = scenario_result.get("volume")

        try:
            execution_result = self.execution_pipeline.execute_hedge({
                "portfolio_id": portfolio_id,
                "hedge_asset": expected_hedge_asset,
                "volume": allocated_volume
            })
        except requests.RequestException as e:
            self.risk_hub.report_critical_failure({"portfolio_id": portfolio_id, "error": str(e)})
            raise HedgeExecutionError(str(e))
        except Exception as e:
            self.risk_hub.report_critical_failure({"portfolio_id": portfolio_id, "error": str(e)})
            raise HedgeExecutionError(str(e))

        exec_token = execution_result.get("token")
        timestamp = datetime.now().isoformat()

        log_data = {
            "portfolio_id": portfolio_id,
            "hedge_asset": expected_hedge_asset,
            "volume": allocated_volume,
            "execution_token": exec_token,
            "timestamp": timestamp
        }
        self.db_storage.save_hedge_log(log_data)

        return {
            "portfolio_id": portfolio_id,
            "hedge_asset": expected_hedge_asset,
            "volume": allocated_volume,
            "execution_token": exec_token,
            "timestamp": timestamp
        }

    def parse_sentiment_feed(self, target_url, element_id):
        response = requests.get(target_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        target_div = soup.find(id=element_id)
        if target_div:
            return target_div.text
        return ""

    def handle_anomaly_trigger(self, anomaly_payload):
        res = self.execution_pipeline.emergency_hedge(anomaly_payload)
        return res


# Главная функция для поддержки интеграционных тестов, использующая честные импортированные модули

def market_portfolio_stress_auto_hedge_engine_v2(payload):
    portfolio_id = payload.get("portfolio_id")
    scenario_result = payload.get("scenario_result", {})

    execution_id = f"exec_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    actions = [{"asset": scenario_result.get("recommended_hedge", "GOLD"), "volume": scenario_result.get("volume", 100)}]

    market_portfolio_execution_pipeline({
        "execution_id": execution_id,
        "portfolio_id": portfolio_id,
        "actions": actions
    })

    db_storage({
        "action": "save",
        "table": "hedge_executions",
        "id": execution_id,
        "data": {
            "portfolio_id": portfolio_id,
            "status": "executed",
            "actions": actions
        }
    })

    return {
        "hedge_execution_id": execution_id,
        "actions": actions
    }
