import hashlib
import os
from bs4 import BeautifulSoup
try:
    from skills.db_storage import db_storage
except ImportError:
    from db_storage import db_storage

def extractor_tool_1790625955(file_path: str, record_id: str) -> dict:
    """
    Модуль извлечения метаданных из разметки.
    Считывает файл, вычисляет хеш контента и сохраняет статус в db_storage.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Извлечение контента (в данном случае всего тела)
    soup = BeautifulSoup(content, 'html.parser')
    text_content = soup.get_text()

    # Вычисление хеша
    content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()

    # Подготовка метаданных
    metadata = {
        "id": record_id,
        "content_hash": content_hash,
        "status": "processed"
    }

    # Интеграция с хранилищем
    storage = db_storage()
    storage.save_record(record_id, metadata)

    return metadata