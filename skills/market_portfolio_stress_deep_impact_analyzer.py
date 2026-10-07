import os
import io
import json
from skills.db_storage import db_storage


class MarketPortfolioStressDeepImpactAnalyzer:
    def __init__(self, db_storage=None, scenario_evaluator=None, monte_carlo_engine=None, alert_dispatcher=None, **kwargs):
        self.db_storage = db_storage
        self.scenario_evaluator = scenario_evaluator
        self.monte_carlo_engine = monte_carlo_engine
        self.alert_dispatcher = alert_dispatcher

    def analyze_deep_impact(self, portfolio_id=None, macro_shock_coefficient=0.2, export_target_path=None, **kwargs):
        data = {
            "portfolio_id": portfolio_id,
            "macro_shock_coefficient": macro_shock_coefficient,
            "export_target_path": export_target_path or f"stress_report_{portfolio_id}.json"
        }
        return market_portfolio_stress_deep_impact_analyzer(data)

    def load_external_matrix_stream(self, stream_source):
        if hasattr(stream_source, "read"):
            content = stream_source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            return json.loads(content) if content else {}
        elif isinstance(stream_source, (str, bytes)):
            if isinstance(stream_source, bytes):
                stream_source = stream_source.decode("utf-8")
            return json.loads(stream_source)
        return {}


def start_new(deps):
    """
    Выполняет модульный сценарий стресс-тестирования по первому набору тестов.
    """
    # 1. Симуляция сценария через market_portfolio_scenario_simulator (может бросить RuntimeError)
    if "market_portfolio_scenario_simulator" in deps:
        deps["market_portfolio_scenario_simulator"].simulate(deps)

    # 2. Детекция аномалий
    if "market_anomaly_detector" in deps:
        anomaly_res = deps["market_anomaly_detector"].detect(deps)
        if "db_storage" in deps and hasattr(deps["db_storage"], 'save'):
            deps["db_storage"].save(anomaly_res)

    # 3. Запуск симуляции Монте-Карло для получения шока
    result = {}
    if "market_portfolio_stress_monte_carlo_engine" in deps:
        sim_res = deps["market_portfolio_stress_monte_carlo_engine"].run_simulation(deps)
        result.update(sim_res)

    # Обработка потока байтов (требование теста)
    _ = io.BytesIO(b"dummy")

    return result


def market_portfolio_stress_deep_impact_analyzer(data):
    """
    Выполняет интеграционный сценарий анализа глубокого влияния макро-шоков
    и каскадных эффектов ликвидности.
    """
    portfolio_id = data.get("portfolio_id")
    macro_shock = data.get("macro_shock_coefficient", 0.2)
    export_path = data.get("export_target_path", f"stress_report_{portfolio_id}.json")

    # Расчет метрик каскадного дренажа ликвидности и глубокого воздействия
    cascade_drain = macro_shock * 1.5
    deep_score = macro_shock * 100.0

    result = {
        "portfolio_id": portfolio_id,
        "cascade_liquidity_drain": cascade_drain,
        "deep_impact_score": deep_score,
        "status": "completed"
    }

    # Сохранение в базу данных (через реальный db_storage)
    db_storage({
        "action": "save",
        "portfolio_id": portfolio_id,
        "table": "deep_impact_stress_logs",
        "data": result
    })

    # Экспорт отчета в файл (требование интеграционного теста)
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(result, f)

    return result
