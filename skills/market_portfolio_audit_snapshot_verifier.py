import json
import hashlib
import logging
import os
from typing import Any, Dict, Optional, Union
from skills.db_storage import MarketParser

logger = logging.getLogger(__name__)

REQUIRED_SNAPSHOT_FIELDS = {"snapshot_id", "portfolio_id", "timestamp", "assets"}


class MarketPortfolioAuditSnapshotVerifier:
    """
    Верификатор снапшотов портфеля для обеспечения непрерывного аудита без заглушек и подавления ошибок.
    """

    def __init__(self, storage_file: Optional[str] = None, db_storage: Optional[Any] = None) -> None:
        if db_storage is not None:
            self.db_storage = db_storage
        elif storage_file is not None:
            self.db_storage = MarketParser(storage_file)
        else:
            self.db_storage = None

    def verify_snapshot_schema(self, snapshot_data: Dict[str, Any]) -> bool:
        """
        Проверяет наличие обязательных полей в структуре снапшота.
        При их отсутствии выбрасывает ValueError.
        """
        if not isinstance(snapshot_data, dict):
            raise ValueError(f"Снапшот должен быть словарем (dict), получен: {type(snapshot_data).__name__}")

        missing_fields = [field for field in REQUIRED_SNAPSHOT_FIELDS if field not in snapshot_data]
        if missing_fields:
            raise ValueError(f"Отсутствуют обязательные поля в снапшоте: {', '.join(sorted(missing_fields))}")

        return True

    def calculate_snapshot_checksum(self, snapshot_data: Dict[str, Any]) -> str:
        """
        Вычисляет SHA-256 контрольную сумму содержимого снапшота без поля 'checksum'.
        """
        payload = {k: v for k, v in snapshot_data.items() if k != "checksum"}
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def verify_snapshot_checksum(self, snapshot_data: Dict[str, Any]) -> bool:
        """
        Сравнивает имеющуюся в снапшоте контрольную сумму с пересчитанной SHA-256.
        Если контрольная сумма отсутствует или не совпадает, выбрасывает ValueError.
        """
        if "checksum" not in snapshot_data:
            raise ValueError("Поле 'checksum' отсутствует в снапшоте")

        expected_checksum = self.calculate_snapshot_checksum(snapshot_data)
        actual_checksum = snapshot_data["checksum"]

        if actual_checksum != expected_checksum:
            raise ValueError(
                f"Несовпадение контрольной суммы: записана {actual_checksum}, ожидалась {expected_checksum}"
            )

        return True

    def verify_snapshot_data(self, snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Полная проверка словаря снапшота: схемы и контрольной суммы.
        Возвращает результат с verification_status = "VALID".
        """
        self.verify_snapshot_schema(snapshot_data)
        self.verify_snapshot_checksum(snapshot_data)

        return {
            "snapshot_id": snapshot_data.get("snapshot_id"),
            "portfolio_id": snapshot_data.get("portfolio_id"),
            "verification_status": "VALID",
            "checksum": snapshot_data.get("checksum"),
        }

    def verify_snapshot_integrity(self, snapshot_id_or_path: str) -> Dict[str, Any]:
        """
        Загружает снапшот из файла/хранилища и выполняет строгую верификацию без заглушек.
        """
        snapshot_data = None
        if self.db_storage is not None and hasattr(self.db_storage, "load_data"):
            loaded = self.db_storage.load_data(snapshot_id_or_path)
            if loaded:
                if isinstance(loaded, list):
                    first_item = loaded[0]
                    if isinstance(first_item, dict):
                        snapshot_data = first_item
                    elif isinstance(first_item, str):
                        try:
                            parsed_lines = json.loads("".join(loaded))
                            if isinstance(parsed_lines, list) and parsed_lines:
                                snapshot_data = parsed_lines[0] if isinstance(parsed_lines[0], dict) else parsed_lines
                            elif isinstance(parsed_lines, dict):
                                snapshot_data = parsed_lines
                        except Exception:
                            pass
                elif isinstance(loaded, dict):
                    snapshot_data = loaded

        if snapshot_data is None and os.path.exists(snapshot_id_or_path):
            with open(snapshot_id_or_path, "r", encoding="utf-8") as f:
                raw_content = f.read().strip()
                if raw_content:
                    parsed = json.loads(raw_content)
                    if isinstance(parsed, list) and parsed:
                        snapshot_data = parsed[0] if isinstance(parsed[0], dict) else parsed
                    elif isinstance(parsed, dict):
                        snapshot_data = parsed

        if snapshot_data is None:
            raise ValueError(f"Снапшот '{snapshot_id_or_path}' не найден или не валиден в хранилище")

        if not isinstance(snapshot_data, dict):
            raise ValueError(f"Загруженный снапшот должен быть словарем, получено: {type(snapshot_data).__name__}")

        return self.verify_snapshot_data(snapshot_data)


# Алиас для класса
PortfolioAuditSnapshotVerifier = MarketPortfolioAuditSnapshotVerifier


def market_portfolio_audit_snapshot_verifier(
    snapshot_input: Union[Dict[str, Any], str],
    storage_file: Optional[str] = None,
    db_storage: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Основная точка входа модуля верификации снапшотов аудита портфеля.
    Принимает либо словарь снапшота, либо путь/ID для загрузки из хранилища.
    """
    verifier = MarketPortfolioAuditSnapshotVerifier(storage_file=storage_file, db_storage=db_storage)
    if isinstance(snapshot_input, dict):
        return verifier.verify_snapshot_data(snapshot_input)
    elif isinstance(snapshot_input, str):
        return verifier.verify_snapshot_integrity(snapshot_input)
    else:
        raise ValueError(f"Неподдерживаемый тип ввода для верификатора: {type(snapshot_input).__name__}")
