import uuid
import os
import json

class AggregatorError(Exception):
    """Кастомное исключение для ошибок агрегации."""
    pass


class StressBacktestAggregatorV2:
    def __init__(self, db_storage, evaluator=None):
        self.db_storage = db_storage
        self.evaluator = evaluator

    def aggregate_stream(self, file_stream):
        content = file_stream.read()
        if not content:
            raise AggregatorError("Empty stream data")
        
        try:
            line = content.decode('utf-8').strip()
            parts = line.split(',')
            if len(parts) != 4:
                raise ValueError("Invalid format")
            
            portfolio_id, scenario_id, metric, val_str = parts
            value = float(val_str)
        except Exception as e:
            raise AggregatorError(f"Malformed stream data: {e}")

        batch_id = uuid.uuid4()
        record = {
            'portfolio_id': portfolio_id,
            'scenario_id': scenario_id,
            'metric': metric,
            'value': value
        }
        
        self.db_storage.save_aggregation(record)

        return {
            'batch_id': batch_id.hex,
            'status': 'SUCCESS',
            'records_processed': 1
        }

    def aggregate_with_evaluation(self, file_stream):
        result = self.aggregate_stream(file_stream)
        if self.evaluator:
            eval_res = self.evaluator.evaluate()
            result['evaluation'] = eval_res
        return result


def aggregate_stress_backtests(payload):
    portfolio_id = payload.get("portfolio_id")
    backtest_ids = payload.get("backtest_ids", [])
    output_path = payload.get("output_path")

    report = {
        "portfolio_id": portfolio_id,
        "processed_backtests": backtest_ids,
        "status": "COMPLETED"
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f)

    return report