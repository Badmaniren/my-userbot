import io
import logging
from typing import List, Optional, Union
from packaging.requirements import Requirement, InvalidRequirement

logger = logging.getLogger(__name__)

def normalize_requirement(raw_req: str, strict: bool = True) -> Optional[str]:
    """
    Нормализует строку зависимости с использованием библиотеки packaging.
    """
    try:
        req = Requirement(raw_req)
        return str(req)
    except (InvalidRequirement, Exception) as e:
        if strict:
            raise ValueError(f"Invalid requirement string: {raw_req}") from e
        return None

def extract_requirements(stream_or_data: Union[io.IOBase, bytes, str], raise_on_error: bool = False) -> List[str]:
    """
    Вспомогательная функция для извлечения требований из потока или данных.
    """
    extractor = PackageRequirementExtractor()
    return extractor.extract_from_stream(stream_or_data, raise_on_error=raise_on_error)

class PackageRequirementExtractor:
    """
    Класс для извлечения и нормализации зависимостей из различных источников (потоки, метаданные).
    """

    def extract_from_stream(self, stream: Union[io.IOBase, bytes, str], raise_on_error: bool = False) -> List[str]:
        requirements = []
        try:
            if isinstance(stream, bytes):
                content = stream.decode('utf-8')
            elif isinstance(stream, str):
                content = stream
            elif hasattr(stream, 'read'):
                data = stream.read()
                if isinstance(data, bytes):
                    content = data.decode('utf-8')
                else:
                    content = str(data)
            else:
                raise TypeError("Unsupported stream type")

            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    normalized = normalize_requirement(line, strict=True)
                    if normalized:
                        requirements.append(normalized)
                except Exception as req_err:
                    if raise_on_error:
                        raise
                    logger.error(f"Failed to parse requirement line '{line}': {req_err}")

        except Exception as e:
            logger.error(f"Error reading requirement stream: {e}")
            if raise_on_error:
                raise
        
        return requirements

    def extract_from_metadata(self, metadata: dict, raise_on_error: bool = False) -> List[str]:
        requirements = []
        raw_dist = metadata.get("requires_dist", [])
        for item in raw_dist:
            try:
                normalized = normalize_requirement(item, strict=True)
                if normalized:
                    requirements.append(normalized)
            except Exception as e:
                if raise_on_error:
                    raise
                logger.error(f"Failed to parse metadata requirement '{item}': {e}")
        return requirements