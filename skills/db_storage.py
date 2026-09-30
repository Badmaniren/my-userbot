import sqlite3

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file: str = "market_data.db"):
        self.storage_file = storage_file

    def fetch_price(self, url: str):
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            return data.get("price")
        except Exception:
            return None

    def parse_html_prices(self, url: str):
        if requests is None or BeautifulSoup is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.find()
            if element and element.text:
                return float(element.text)
        except Exception:
            pass
        return None

    def fetch_and_store(self, symbol: str, price: float):
        conn = sqlite3.connect(self.storage_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        
        cursor.execute(
            'INSERT INTO market_data (symbol, price) VALUES (?, ?)',
            (symbol, price)
        )
        
        conn.commit()
        conn.close()

    def load_data(self, filename: str):
        if filename.endswith('.db'):
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT symbol, price FROM market_data')
                rows = cursor.fetchall()
                data = [f"{row[0]},{row[1]}\n" for row in rows]
            finally:
                conn.close()
            return data
        else:
            with open(filename, 'rb') as f:
                lines = f.readlines()
                return [line.decode('utf-8') for line in lines]


class DBStorage:
    def __init__(self):
        self._storage = {}
        self._portfolios = {}
        self._orders = {}
        self._records = {}
        self._reports = {}
        self._evaluations = {}
        self._simulations = {}
        self._risk_metrics = {}
        self._stress_results = {}

    def save_portfolio(self, portfolio_id, data):
        self._portfolios[portfolio_id] = data

    def get_portfolio(self, portfolio_id):
        return self._portfolios.get(portfolio_id)

    def load_portfolio(self, portfolio_id):
        return self.get_portfolio(portfolio_id)

    def fetch_portfolio(self, portfolio_id):
        res = self.get_portfolio(portfolio_id)
        if res is not None:
            return res
        return {"portfolio_id": portfolio_id, "initial_value": 100000.0, "volatility": 0.2, "drift": 0.0}

    def save_orders(self, portfolio_id, orders):
        self._orders[portfolio_id] = orders

    def get_orders(self, portfolio_id):
        return self._orders.get(portfolio_id)

    def save_record(self, record_id, data):
        self._records[record_id] = data

    def get_record(self, record_id):
        return self._records.get(record_id)

    def save(self, key, value):
        self._storage[key] = value

    def get(self, key, default=None):
        return self._storage.get(key, default)

    def save_portfolio_position(self, portfolio_id, position):
        if portfolio_id not in self._portfolios:
            self._portfolios[portfolio_id] = {"assets": {}}
        if isinstance(self._portfolios[portfolio_id], dict):
            assets = self._portfolios[portfolio_id].setdefault("assets", {})
            if isinstance(position, dict):
                assets.update(position)

    def persist_state(self, key, state):
        self._storage[key] = state

    def load_state(self, key):
        return self._storage.get(key)

    def fetch_stream(self, *args, **kwargs):
        import io
        return io.BytesIO(b"data")

    def load_binary_stream(self, portfolio_id, simulations_count=0):
        import io
        import uuid
        return io.BytesIO(uuid.uuid4().bytes + b"\x00" * 32)

    def __call__(self, action_or_payload, *args, **kwargs):
        if isinstance(action_or_payload, dict):
            payload = action_or_payload
            action = payload.get("action")
            table = payload.get("table", "default")
            portfolio_id = payload.get("portfolio_id") or payload.get("id")

            if action in ("set", "save", "store"):
                data = payload.get("data", payload)
                if table not in self._storage:
                    self._storage[table] = {}
                if portfolio_id:
                    self._storage[table][portfolio_id] = data
                return data
            elif action in ("get", "load", "fetch"):
                if table in self._storage and portfolio_id in self._storage[table]:
                    return self._storage[table][portfolio_id]
                return {"portfolio_id": portfolio_id}
            return {}

        if isinstance(action_or_payload, str):
            action = action_or_payload
            if action == "save_portfolio":
                if args and isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
                    pid, data = args[0]
                elif len(args) >= 2:
                    pid, data = args[0], args[1]
                else:
                    return None
                self.save_portfolio(pid, data)
                return data

            elif action == "get_portfolio":
                pid = args[0] if args else kwargs.get("portfolio_id")
                return self.get_portfolio(pid)

            elif action == "get_target_weights":
                pid = args[0] if args else kwargs.get("portfolio_id")
                port = self.get_portfolio(pid)
                if isinstance(port, dict):
                    if "assets" in port and isinstance(port["assets"], dict):
                        weights = {}
                        for sym, data in port["assets"].items():
                            if isinstance(data, dict):
                                weights[sym] = data.get("target_weight", 0.0)
                            else:
                                weights[sym] = data
                        return weights
                    return port
                return port

            elif action == "save_orders":
                if args and isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
                    pid, orders = args[0]
                elif len(args) >= 2:
                    pid, orders = args[0], args[1]
                else:
                    return None
                self.save_orders(pid, orders)
                return orders

            elif action == "get_orders":
                pid = args[0] if args else kwargs.get("portfolio_id")
                return self.get_orders(pid)

            elif action in ("save", "set"):
                if len(args) >= 2:
                    self.save(args[0], args[1])
                elif args:
                    self.save(args[0], True)
                return True

            elif action in ("get", "fetch"):
                if args:
                    return self.get(args[0])

        return None


DbStorage = DBStorage
db_storage = DBStorage()


class DatabaseConnection:
    def __init__(self, db_path="default.db"):
        self.db_path = db_path


def save_portfolio_state(portfolio_id, state):
    db_storage.save_portfolio(portfolio_id, state)


def get_portfolio_state(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def save_to_db(key, data):
    db_storage.save(key, data)


def fetch_from_db(key):
    return db_storage.get(key)


def save_report_to_db(report_id, report):
    db_storage._reports[report_id] = report


def get_report_from_db(report_id):
    return db_storage._reports.get(report_id)


def save_macro_evaluation(portfolio_id, evaluation):
    db_storage._evaluations[portfolio_id] = evaluation


def get_macro_evaluation(portfolio_id):
    return db_storage._evaluations.get(portfolio_id)


def save_portfolio_data(portfolio_id, data):
    db_storage.save_portfolio(portfolio_id, data)


def get_portfolio_data(portfolio_id):
    return db_storage.get_portfolio(portfolio_id)


def save_simulation_results(sim_id, results):
    db_storage._simulations[sim_id] = results


def get_simulation_results(sim_id):
    return db_storage._simulations.get(sim_id)


def save_portfolio_risk_metrics(portfolio_id, metrics):
    db_storage._risk_metrics[portfolio_id] = metrics


def get_portfolio_risk_metrics(portfolio_id):
    return db_storage._risk_metrics.get(portfolio_id)


def fetch_portfolio(portfolio_id):
    return db_storage.fetch_portfolio(portfolio_id)


def save_stress_test_result(simulation_id, result_data):
    db_storage._stress_results[simulation_id] = result_data


def get_stress_test_result(simulation_id):
    return db_storage._stress_results.get(simulation_id)
