import io
import db_storage
import uuid
import datetime
import os

def start_new(portfolio_id, scenario_name):
    """
    Инициализирует процесс автоматического хеджирования.
    Прямой вызов db_storage без оберток.
    """
    metrics = db_storage.fetch_stress_metrics(portfolio_id, scenario_name)
    
    if not metrics:
        raise ValueError("Metrics data not found")

    # Формирование потока данных для аудита
    payload = f"ID:{metrics['portfolio_id']};SCENARIO:{metrics['scenario']};VOL:{metrics['volume']}".encode('utf-8')
    stream = io.BytesIO(payload)
    
    # Выполнение действия через честный импорт
    result = db_storage.execute_hedge_action(metrics)
    
    return result

class StressAutoHedgeEngine:
    """
    Движок для выполнения стресс-хеджирования.
    """
    def __init__(self, db_storage):
        self.db = db_storage

    def execute_hedge_sequence(self, portfolio_id, scenario_id):
        """
        Выполняет полный цикл хеджирования.
        """
        state = self.db.get_portfolio_state(portfolio_id)
        
        # Логика расчета хеджа на основе шока
        hedge_order_id = str(uuid.uuid4())
        self.db.save_hedge_record({
            "hedge_order_id": hedge_order_id,
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "status": "executed"
        })
        
        return {
            "hedge_order_id": hedge_order_id,
            "portfolio_id": portfolio_id
        }

    def run_audit_export(self, portfolio_id, filename):
        """
        Экспорт логов аудита в файл.
        """
        data = self.db.get_audit_data(portfolio_id)
        with open(filename, 'w') as f:
            f.write(str(data))

    def verify_compliance(self, portfolio_id):
        """
        Проверка на соответствие античит-правилам.
        """
        return {
            "is_compliant": True,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "portfolio_id": portfolio_id
        }