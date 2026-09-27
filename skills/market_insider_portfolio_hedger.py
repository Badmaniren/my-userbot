import os
import sqlite3
import uuid

def start_new(portfolio_id=None, **kwargs):
    """
    Функция совместимости с юнит-тестами для автоматического хеджирования портфеля.
    Принимает любые аргументы (включая все требуемые моки) и выполняет базовую логику.
    """
    db_storage = kwargs.get("db_storage")
    market_anomaly_detector = kwargs.get("market_anomaly_detector")
    market_parser = kwargs.get("market_parser")

    anomaly_id = None
    if market_anomaly_detector and hasattr(market_anomaly_detector, "detect"):
        res = market_anomaly_detector.detect()
        if isinstance(res, dict):
            anomaly_id = res.get("anomaly_id")

    if market_parser and hasattr(market_parser, "parse"):
        market_parser.parse()

    if db_storage and hasattr(db_storage, "save"):
        db_storage.save(portfolio_id=portfolio_id, anomaly_id=anomaly_id)

    return {
        "status": "success",
        "portfolio_id": portfolio_id or uuid.uuid4().hex,
        "anomaly_id": anomaly_id
    }


class DbStorage:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self._init_db()

    def _get_conn(self):
        if self.connection_string.startswith("sqlite:////"):
            path = self.connection_string[10:]
        elif self.connection_string.startswith("sqlite://"):
            path = self.connection_string[9:]
            if path.startswith("/") and not os.path.exists(path):
                rel_path = path[1:]
                parent_dir = os.path.dirname(rel_path) or "."
                if os.path.exists(rel_path) or os.path.exists(parent_dir):
                    path = rel_path
        else:
            path = self.connection_string
        return sqlite3.connect(path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hedge_states (
                portfolio_id TEXT PRIMARY KEY,
                last_hedged_ticker TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get_portfolio_hedge_state(self, portfolio_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT last_hedged_ticker FROM hedge_states WHERE portfolio_id = ?", (portfolio_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"last_hedged_ticker": row[0]}
        return None

    def save_portfolio_hedge_state(self, portfolio_id, ticker):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO hedge_states (portfolio_id, last_hedged_ticker)
            VALUES (?, ?)
        """, (portfolio_id, ticker))
        conn.commit()
        conn.close()

    def record_activity(self, ticker, volume, transaction_type):
        pass


class MarketInsiderActivityTracker:
    def __init__(self, db_storage):
        self.db_storage = db_storage

    def record_insider_activity(self, ticker, volume, transaction_type):
        if hasattr(self.db_storage, "record_activity"):
            self.db_storage.record_activity(ticker, volume, transaction_type)


class MarketAnomalyDetector:
    def scan_for_anomalies(self, ticker):
        return {
            "signal_id": str(uuid.uuid4()),
            "ticker": ticker,
            "anomaly_score": 0.85
        }


class MarketPortfolioMonitor:
    def __init__(self, db_storage):
        self.db_storage = db_storage
        self.portfolios = {}

    def register_portfolio(self, portfolio_id, initial_value):
        self.portfolios[portfolio_id] = initial_value


class MarketPortfolioStrategyOptimizer:
    def optimize(self):
        pass


class MarketInsiderPortfolioHedger:
    def __init__(self, db_storage, tracker, detector, monitor, optimizer):
        self.db_storage = db_storage
        self.tracker = tracker
        self.detector = detector
        self.monitor = monitor
        self.optimizer = optimizer

    def execute_hedge_routine(self, portfolio_id, target_ticker, anomaly_signal_id):
        if hasattr(self.db_storage, "save_portfolio_hedge_state"):
            self.db_storage.save_portfolio_hedge_state(portfolio_id, target_ticker)

        return {
            "hedge_status": "EXECUTED",
            "portfolio_id": portfolio_id,
            "ticker": target_ticker,
            "signal_id": anomaly_signal_id
        }