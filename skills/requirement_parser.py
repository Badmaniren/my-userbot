import re

def parse_requirement(raw_req: str):
    """
    Парсит строку зависимости PyPI (например, 'requests (>=2.0.0)' или 'pkg[extra] >=1.0, <2.0')
    и возвращает кортеж (имя_пакета, список_ограничений).
    """
    # Очищаем строку от лишних пробелов
    line = raw_req.strip()
    if not line:
        return "", []

    # Удаляем экстра-фичи в квадратных скобках, например, requests[security] -> requests
    line = re.sub(r'\[.*?\]', '', line)

    # Сначала проверим вариант со скобками: pkg (>=1.0.0, <2.0.0) или pkg (==1.0)
    match_with_parens = re.match(r'^([A-Za-z0-9_.-]+)\s*\((.*?)\)$', line)
    
    if match_with_parens:
        name = match_with_parens.group(1).strip()
        constraints_str = match_with_parens.group(2).strip()
    else:
        # Вариант без скобок: pkg >=1.0.0, <2.0.0 или просто pkg
        parts = re.split(r'\s+([<>=!~]=?|[<>])\s*', line, maxsplit=1)
        name = parts[0].strip()
        if len(parts) > 1:
            constraints_str = "".join(parts[1:])
        else:
            constraints_str = ""

    if not constraints_str:
        return name, []

    # Парсим список ограничений, разделенных запятыми
    constraints = []
    raw_constraints = constraints_str.split(',')
    
    op_ver_pattern = re.compile(r'^\s*([<>=!~]=?|[<>])\s*([A-Za-z0-9_.-]+)\s*$')
    
    for rc in raw_constraints:
        rc = rc.strip()
        if not rc:
            continue
        m = op_ver_pattern.match(rc)
        if m:
            constraints.append((m.group(1), m.group(2)))
        else:
            sub_m = re.match(r'^([<>=!~]=?|[<>])\s*(.*)$', rc)
            if sub_m:
                constraints.append((sub_m.group(1), sub_m.group(2).strip()))

    return name, constraints