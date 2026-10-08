import sqlite3
import json
import math

from skills.db_storage import DbStorage


class MarketAnomalyDetector:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def register_anomaly(self, asset_ticker, anomaly_score, anomaly_type):
        if self.db_storage and hasattr(self.db_storage, 'conn'):
            with self.db_storage.conn:
                self.db_storage.conn.execute(
                    "INSERT INTO market_anomalies (asset_ticker, anomaly_score, anomaly_type) VALUES (?, ?, ?)",
                    (asset_ticker, anomaly_score, anomaly_type)
                )

    def get_anomaly(self, asset_ticker):
        if self.db_storage and hasattr(self.db_storage, 'conn'):
            cursor = self.db_storage.conn.cursor()
            cursor.execute("SELECT * FROM market_anomalies WHERE asset_ticker = ?", (asset_ticker,))
            row = cursor.fetchone()
            if row:
                return {
                    "asset_ticker": row["asset_ticker"],
                    "anomaly_score": row["anomaly_score"],
                    "anomaly_type": row["anomaly_type"]
                }
        return {"anomaly_score": 0.5}


class MarketInsiderActivityTracker:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def log_insider_transaction(self, asset_ticker, transaction_type, volume, insider_role):
        if self.db_storage and hasattr(self.db_storage, 'conn'):
            with self.db_storage.conn:
                self.db_storage.conn.execute(
                    "INSERT INTO insider_transactions (asset_ticker, transaction_type, volume, insider_role) VALUES (?, ?, ?, ?)",
                    (asset_ticker, transaction_type, volume, insider_role)
                )

    def get_activity(self, asset_ticker):
        if self.db_storage and hasattr(self.db_storage, 'conn'):
            cursor = self.db_storage.conn.cursor()
            cursor.execute("SELECT SUM(volume) as total_vol FROM insider_transactions WHERE asset_ticker = ?", (asset_ticker,))
            row = cursor.fetchone()
            if row and row["total_vol"]:
                return {"multiplier": 1.5, "total_volume": row["total_vol"]}
        return {"multiplier": 1.2}


class MarketPortfolioValuation:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def save_portfolio_valuation(self, portfolio_id, total_value, asset_allocations):
        if self.db_storage:
            self.db_storage.save_portfolio_valuation(portfolio_id, total_value, asset_allocations)

    def get_valuation(self, portfolio_id):
        if self.db_storage:
            return self.db_storage.get_portfolio_valuation(portfolio_id)
        return None


class MarketPortfolioAnomalyHedgingCalculator:
    def __init__(self, db_storage=None, anomaly_detector=None, insider_tracker=None, portfolio_valuation=None):
        self.db_storage = db_storage
        self.anomaly_detector = anomaly_detector or MarketAnomalyDetector(db_storage)
        self.insider_tracker = insider_tracker or MarketInsiderActivityTracker(db_storage)
        self.portfolio_valuation = portfolio_valuation or MarketPortfolioValuation(db_storage)

    def calculate_beta(self, portfolio_returns, asset_returns):
        n = len(asset_returns)
        if n == 0 or len(portfolio_returns) != n:
            return 0.0
        mean_asset = sum(asset_returns) / n
        mean_portfolio = sum(portfolio_returns) / n

        covariance = sum((asset_returns[i] - mean_asset) * (portfolio_returns[i] - mean_portfolio) for i in range(n))
        variance_asset = sum((asset_returns[i] - mean_asset) ** 2 for i in range(n))

        if abs(variance_asset) < 1e-12:
            return 0.0
        return covariance / variance_asset

    def estimate_beta_sensitivity(self, portfolio_returns, asset_returns):
        return self.calculate_beta(portfolio_returns, asset_returns)

    def calculate_beta_sensitivity(self, portfolio_returns, asset_returns):
        return self.calculate_beta(portfolio_returns, asset_returns)

    def calculate_hedging_volume(self, portfolio_value, beta, asset_price, insider_multiplier):
        if asset_price == 0:
            return 0.0
        return (portfolio_value * abs(beta) * insider_multiplier) / asset_price

    def calculate_protective_position_volume(self, portfolio_value, beta, asset_price, insider_multiplier):
        return self.calculate_hedging_volume(portfolio_value, beta, asset_price, insider_multiplier)

    def calculate_hedging(self, portfolio, anomaly_data, insider_activity):
        return self.calculate_hedging_parameters_full(portfolio, anomaly_data, insider_activity)

    def analyze_and_hedge(self, portfolio, anomaly_data, insider_activity):
        return self.calculate_hedging_parameters_full(portfolio, anomaly_data, insider_activity)

    def calculate_hedging_parameters_full(self, portfolio, anomaly_data, insider_activity):
        asset_name = anomaly_data.get("asset") or anomaly_data.get("asset_ticker", "UNKNOWN")
        asset_returns = anomaly_data.get("returns", [0.01, -0.01])
        portfolio_returns = portfolio.get("portfolio_returns", [0.01, -0.01])

        beta = self.calculate_beta(portfolio_returns, asset_returns)
        portfolio_val = portfolio.get("total_value", 100000.0)
        current_price = anomaly_data.get("current_price", 100.0)
        multiplier = insider_activity.get("multiplier", 1.5)

        hedge_vol = self.calculate_hedging_volume(portfolio_val, beta, current_price, multiplier)

        return {
            "beta": beta,
            "hedge_volume": hedge_vol,
            "asset": asset_name
        }

    def calculate_hedging_parameters(self, portfolio_id=None, anomalous_asset=None, asset_beta=None, portfolio=None, anomaly_data=None, insider_activity=None):
        # Case 1: First argument passed as portfolio dictionary
        if isinstance(portfolio_id, dict):
            p = portfolio_id
            a = anomalous_asset if isinstance(anomalous_asset, dict) else (anomaly_data or {})
            i = asset_beta if isinstance(asset_beta, dict) else (insider_activity or {})
            return self.calculate_hedging_parameters_full(p, a, i)

        # Case 2: Explicit portfolio dictionary via keyword or secondary positional args
        if portfolio is not None or (anomaly_data is not None and not isinstance(portfolio_id, str)):
            p = portfolio or portfolio_id or {}
            a = anomaly_data or anomalous_asset or {}
            i = insider_activity or {}
            return self.calculate_hedging_parameters_full(p, a, i)

        # Case 3: Portfolio ID passed as string (integration flow)
        if portfolio_id is not None and anomalous_asset is not None:
            valuation = self.portfolio_valuation.get_valuation(portfolio_id)
            total_value = valuation["total_value"] if valuation else 1000000.0
            allocations = valuation["asset_allocations"] if valuation else {anomalous_asset: 0.1}
            asset_weight = allocations.get(anomalous_asset, 0.1)

            anomaly = self.anomaly_detector.get_anomaly(anomalous_asset)
            anomaly_score = anomaly.get("anomaly_score", 0.8) if anomaly else 0.8

            insider = self.insider_tracker.get_activity(anomalous_asset)
            multiplier = insider.get("multiplier", 1.5) if insider else 1.5

            beta = asset_beta if asset_beta is not None else 1.0
            risk_factor = 1.0 + anomaly_score * (multiplier - 1.0)

            expected_asset_value = total_value * asset_weight
            required_hedge_volume = expected_asset_value * beta * risk_factor

            result = {
                "portfolio_id": portfolio_id,
                "anomalous_asset": anomalous_asset,
                "beta_sensitivity": beta,
                "required_hedge_volume": required_hedge_volume,
                "risk_factor": risk_factor
            }

            if self.db_storage and hasattr(self.db_storage, 'save_hedging_calculation'):
                self.db_storage.save_hedging_calculation(
                    portfolio_id, anomalous_asset, beta, required_hedge_volume, risk_factor
                )

            return result
        else:
            p = portfolio or {}
            a = anomaly_data or {}
            i = insider_activity or {}
            return self.calculate_hedging_parameters_full(p, a, i)
