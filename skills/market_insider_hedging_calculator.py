import json
import requests

class MarketInsiderHedgingCalculator:
    """
    Модуль для вычисления оптимальных параметров хеджирования
    на основе инсайдерских аномалий.
    """

    def __init__(self, db_storage=None, anomaly_analyzer=None, portfolio_valuation=None, valuation_service=None):
        self.db_storage = db_storage
        self.anomaly_analyzer = anomaly_analyzer or anomaly_analyzer
        self.portfolio_valuation = portfolio_valuation or valuation_service
        self.multiplier = 1.0
        self.min_threshold = 0.0

    def calculate_hedging_parameters(self, portfolio_id, anomaly_id, risk_tolerance):
        if not (0.0 <= risk_tolerance <= 1.0):
            raise ValueError("Risk tolerance must be between 0 and 1")

        exposure_data = self.portfolio_valuation.get_portfolio_exposure(portfolio_id)
        anomaly_data = self.anomaly_analyzer.get_anomaly_details(anomaly_id)

        if anomaly_data is None:
            raise KeyError("Anomaly not found")

        asset_exposure = exposure_data.get("asset_exposure", 0.0)
        if asset_exposure <= 0:
            return {"hedging_volume": 0.0, "status": "NO_HEDGING_REQUIRED"}

        anomaly_score = anomaly_data.get("anomaly_score", 0.0)
        hedging_volume = asset_exposure * anomaly_score * (1.0 - risk_tolerance)

        result = {
            "portfolio_id": portfolio_id,
            "anomaly_id": anomaly_id,
            "asset": exposure_data.get("asset"),
            "hedging_volume": hedging_volume
        }

        if self.db_storage:
            self.db_storage.save_hedging_strategy(result)

        return result

    def calculate_hedging_strategy(self, portfolio_valuation, anomaly_analysis, risk_tolerance):
        """Интеграционный метод для обработки данных анализатора."""
        total_cost = 0.0
        positions = []

        for anomaly in anomaly_analysis:
            asset = anomaly.get("asset")
            score = anomaly.get("anomaly_score", 0.5)
            # Логика расчета на основе интеграционных данных
            cost = score * (1.0 - risk_tolerance) * 10000
            total_cost += cost
            positions.append({"asset": asset, "cost": cost})

        return {
            "portfolio_id": portfolio_valuation.get("portfolio_id"),
            "hedging_positions": positions,
            "total_hedging_cost": total_cost,
            "recommended_hedge_ratio": min(total_cost / 50000, 1.0)
        }

    def load_config_from_stream(self, stream):
        data = json.load(stream)
        self.multiplier = data.get("multiplier", 1.0)
        self.min_threshold = data.get("min_threshold", 0.0)

    def export_report_to_stream(self, stream, report_data):
        def _round_floats(obj):
            if isinstance(obj, float):
                return round(obj, 2)
            elif isinstance(obj, dict):
                return {k: _round_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_round_floats(item) for item in obj]
            return obj

        formatted_data = _round_floats(report_data)
        content = json.dumps(formatted_data)
        stream.write(content.encode('utf-8'))

    def calculate_and_execute_hedging(self, portfolio_id, anomaly_id, risk_tolerance, execution_endpoint):
        params = self.calculate_hedging_parameters(portfolio_id, anomaly_id, risk_tolerance)
        response = requests.post(execution_endpoint, json=params)

        if response.status_code == 200:
            data = response.json()
            return {
                "execution_status": "success",
                "transaction_id": data.get("transaction_id")
            }
        return {"execution_status": "failed"}