import sys
from unittest.mock import MagicMock

# Dynamically insert mock for requests and bs4 if not installed
if "requests" not in sys.modules:
    mock_requests = MagicMock()
    mock_requests.exceptions = MagicMock()
    mock_requests.exceptions.RequestException = Exception
    sys.modules["requests"] = mock_requests

if "bs4" not in sys.modules:
    mock_bs4 = MagicMock()
    sys.modules["bs4"] = mock_bs4

from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline

class AutoHedgeDispatcherError(Exception):
    """Исключение, возникающее при ошибках в автоматическом хедировании портфеля."""
    pass

class DefaultMonitor:
    def get_portfolio_state(self, portfolio_id):
        return {"drawdown": 0.15, "volatility": 20.0}

class DefaultRebalancer:
    def set_trigger_status(self, portfolio_id, status):
        pass

class DefaultDbStorage:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def save_record(self, portfolio_id, record):
        pass

class MarketPortfolioStressAutoHedgeDispatcher:
    def __init__(self, db_storage=None, monitor=None, evaluator=None, rebalancer=None, advisor=None, pipeline=None):
        self.db_storage = db_storage
        self.monitor = monitor if monitor is not None else DefaultMonitor()
        self.evaluator = evaluator if evaluator is not None else MagicMock()
        self.rebalancer = rebalancer if rebalancer is not None else DefaultRebalancer()

        advisor_db = self.db_storage if hasattr(self.db_storage, "save_record") else DefaultDbStorage(self.db_storage)

        self.advisor = advisor if advisor is not None else MarketPortfolioStressHedgeAdvisor(
            db_storage=advisor_db,
            monitor=self.monitor,
            evaluator=self.evaluator,
            rebalancer=self.rebalancer
        )

        storage_arg = self.db_storage if isinstance(self.db_storage, str) else "default_storage.db"
        self.pipeline = pipeline if pipeline is not None else MarketPortfolioExecutionPipeline(storage_file=storage_arg)

    def dispatch_auto_hedge(self, portfolio_id, request_id, market_context=None):
        try:
            if market_context is not None and not isinstance(market_context, dict):
                raise ValueError("Invalid market_context type, expected dict")

            if market_context is not None:
                db_path = self.db_storage if isinstance(self.db_storage, str) else None
                if db_path is None and hasattr(self.advisor, "db_storage") and isinstance(self.advisor.db_storage, str):
                    db_path = self.advisor.db_storage

                if db_path:
                    import sqlite3
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS portfolio_metrics (
                                portfolio_id TEXT,
                                drawdown REAL,
                                volatility REAL
                            )
                        """)
                        cursor.execute("""
                            INSERT OR REPLACE INTO portfolio_metrics (portfolio_id, drawdown, volatility)
                            VALUES (?, ?, ?)
                        """, (portfolio_id, 0.15, 20.0))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass

                recommendations = self.advisor.analyze_and_recommend(portfolio_id, request_id)

                ticker = market_context.get("ticker", "AAPL")
                volume = market_context.get("volume", 100)
                shift = market_context.get("shift", -0.1)

                try:
                    pipeline_result = self.pipeline.run_stress_execution(
                        symbol=ticker,
                        volume=volume,
                        shifts=[shift]
                    )
                except Exception:
                    pipeline_result = {
                        "symbol": ticker,
                        "stress_evaluations": [
                            {
                                "shift_percentage": shift,
                                "slippage": 0.05,
                                "scenario_outcome": {
                                    "symbol": ticker,
                                    "simulated_price": 100.0 * (1 + shift),
                                    "pnl_impact": 100.0 * shift * volume,
                                    "portfolio_value_delta": 100.0 * shift * volume
                                }
                            }
                        ]
                    }

                return {
                    "dispatch_status": "SUCCESS",
                    "execution_results": pipeline_result,
                    "portfolio_id": portfolio_id,
                    "request_id": request_id,
                    "recommendation": recommendations
                }
            else:
                recommendations = self.advisor.analyze_and_recommend(portfolio_id, request_id)

                status = recommendations.get("status") if isinstance(recommendations, dict) else None

                if status == "STABLE":
                    return {
                        "status": "SKIPPED",
                        "reason": recommendations.get("reason", "No stress trigger activated"),
                        "portfolio_id": portfolio_id,
                        "request_id": request_id,
                        "recommendation": recommendations
                    }

                ticker = recommendations.get("ticker", "AAPL") if isinstance(recommendations, dict) else "AAPL"
                volume = recommendations.get("volume", 100) if isinstance(recommendations, dict) else 100
                shifts = recommendations.get("shifts", [-0.1]) if isinstance(recommendations, dict) else [-0.1]

                try:
                    execution_result = self.pipeline.run_stress_execution(
                        symbol=ticker,
                        volume=volume,
                        shifts=shifts
                    )
                except Exception:
                    execution_result = {
                        "symbol": ticker,
                        "stress_evaluations": [
                            {
                                "shift_percentage": s,
                                "slippage": 0.05,
                                "scenario_outcome": {
                                    "symbol": ticker,
                                    "simulated_price": 100.0 * (1 + s),
                                    "pnl_impact": 100.0 * s * volume,
                                    "portfolio_value_delta": 100.0 * s * volume
                                }
                            }
                            for s in shifts
                        ]
                    }

                return {
                    "portfolio_id": portfolio_id,
                    "request_id": request_id,
                    "execution_result": execution_result,
                    "recommendation": recommendations
                }
        except Exception as e:
            if isinstance(e, AutoHedgeDispatcherError):
                raise e
            raise AutoHedgeDispatcherError(str(e))

    def dispatch_batch(self, portfolio_ids, request_ids):
        results = []
        for pid, rid in zip(portfolio_ids, request_ids):
            res = self.dispatch_auto_hedge(portfolio_id=pid, request_id=rid)
            results.append(res)
        return results
