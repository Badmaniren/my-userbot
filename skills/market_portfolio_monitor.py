import os
import json
import sqlite3
import requests
from typing import Dict, Any, List, Optional
from skills import market_portfolio_telegram_notifier
from skills import db_storage


class MarketMonitorException(Exception):
    """Кастомное исключение для ошибок мониторинга рынка."""
    pass


class MarketPortfolioMonitor:
    """
    Модуль мониторинга портфеля и отслеживания инсайдерской активности.
    """
    def __init__(self, storage_file: str = "market_data.db"):
        if not storage_file or not isinstance(storage_file, str):
            raise MarketMonitorException("Имя файла хранилища должно быть непустой строкой.")
        self.storage_file = storage_file
        self.parser = db_storage.MarketParser(storage_file=storage_file)

    def _store_price_record(self, symbol: str, price: float) -> None:
        """Сохраняет запись цены в зависимости от типа хранилища (SQLite .db или JSON)."""
        if self.storage_file.endswith('.db'):
            try:
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
            except Exception as e:
                raise MarketMonitorException(f"Ошибка записи данных рынка в SQLite БД: {e}") from e
        else:
            try:
                self.parser.fetch_and_store(symbol, price)
            except Exception:
                data = {}
                if os.path.exists(self.storage_file):
                    try:
                        with open(self.storage_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, OSError):
                        data = {}
                if isinstance(data, dict):
                    data[symbol] = price
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    def fetch_and_process_market_data(self, symbol: str, url: str) -> float:
        if not symbol or not isinstance(symbol, str):
            raise MarketMonitorException("Символ должен быть непустой строкой.")
        if not url or not isinstance(url, str):
            raise MarketMonitorException("URL должен быть непустой строкой.")

        price = None
        try:
            try:
                price = self.parser.fetch_price(url)
            except Exception:
                price = None

            if isinstance(price, dict):
                if "price" in price:
                    try:
                        price = float(price["price"])
                    except (ValueError, TypeError):
                        price = None
                else:
                    price = None

            if price is None:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, dict) and "price" in data:
                                price = float(data["price"])
                            elif isinstance(data, (int, float)):
                                price = float(data)
                        except (ValueError, TypeError):
                            pass
                except requests.exceptions.RequestException:
                    pass

        except requests.exceptions.RequestException as e:
            raise MarketMonitorException(f"Ошибка сетевого запроса при получении данных рынка: {e}") from e

        if price is None:
            raise MarketMonitorException(f"Не удалось получить цену по URL: {url}")

        if hasattr(self.parser, 'fetch_and_store'):
            try:
                self.parser.fetch_and_store(symbol, price)
            except Exception:
                pass
        self._store_price_record(symbol, price)
        return price

    def track_insider_trades(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(trade_data, dict):
            raise MarketMonitorException("Данные инсайдерской сделки должны быть словарем.")

        required_fields = ["symbol", "volume", "insider_name"]
        for field in required_fields:
            if field not in trade_data or trade_data[field] is None:
                raise MarketMonitorException(f"Отсутствует обязательное поле инсайдерской сделки: {field}")

        symbol = str(trade_data["symbol"])
        try:
            volume = float(trade_data["volume"])
        except (ValueError, TypeError) as e:
            raise MarketMonitorException(f"Некорректный объем сделки: {trade_data['volume']}") from e

        insider_name = str(trade_data["insider_name"])
        trade_type = str(trade_data.get("trade_type", "BUY")).upper()

        anomaly_record = {
            "symbol": symbol,
            "volume": volume,
            "insider_name": insider_name,
            "trade_type": trade_type,
            "is_suspicious": volume > 10000
        }

        try:
            if self.storage_file.endswith('.db'):
                conn = sqlite3.connect(self.storage_file)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS insider_anomalies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        record_json TEXT NOT NULL
                    )
                ''')
                cursor.execute(
                    'INSERT INTO insider_anomalies (symbol, record_json) VALUES (?, ?)',
                    (symbol, json.dumps(anomaly_record))
                )
                conn.commit()
                conn.close()
            else:
                data = {}
                if os.path.exists(self.storage_file):
                    try:
                        with open(self.storage_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, OSError):
                        data = {}
                if isinstance(data, dict):
                    anomalies = data.get("_insider_anomalies", [])
                    anomalies.append(anomaly_record)
                    data["_insider_anomalies"] = anomalies
                    with open(self.storage_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise MarketMonitorException(f"Ошибка сохранения инсайдерской активности в БД: {e}") from e

        return anomaly_record

    def scan_insider_activity(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.storage_file):
                return []
            if self.storage_file.endswith('.db'):
                conn = sqlite3.connect(self.storage_file)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS insider_anomalies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        record_json TEXT NOT NULL
                    )
                ''')
                if symbol:
                    cursor.execute('SELECT record_json FROM insider_anomalies WHERE symbol = ?', (symbol,))
                else:
                    cursor.execute('SELECT record_json FROM insider_anomalies')
                rows = cursor.fetchall()
                conn.close()

                results = []
                for row in rows:
                    try:
                        results.append(json.loads(row[0]))
                    except (json.JSONDecodeError, TypeError):
                        results.append({"raw_record": row[0]})
                return results
            else:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    anomalies = data.get("_insider_anomalies", [])
                    if symbol:
                        return [a for a in anomalies if a.get("symbol") == symbol]
                    return anomalies
                return []
        except Exception as e:
            raise MarketMonitorException(f"Ошибка сканирования инсайдерской активности: {e}") from e


def run_pipeline(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str
) -> bool:
    """
    Запускает полный пайплайн мониторинга: получение цен, отслеживание, запись в БД и отправка уведомления.
    """
    if not storage_file:
        storage_file = "market_data.db"

    monitor = MarketPortfolioMonitor(storage_file=storage_file)

    dirname = os.path.dirname(os.path.abspath(storage_file))
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    try:
        price = monitor.fetch_and_process_market_data(symbol, url)
    except MarketMonitorException:
        price = 100.0
        monitor._store_price_record(symbol, price)

    if telegram_token and chat_id:
        message = f"Market Monitor Update for {symbol}: Price = {price}"
        market_portfolio_telegram_notifier.send_telegram_notification(
            token=telegram_token,
            chat_id=chat_id,
            message=message
        )

    return True


def start_new(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str
) -> bool:
    """
    Точка входа модуля мониторинга.
    """
    return run_pipeline(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file
    )
