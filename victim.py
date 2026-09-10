def solve_task(a, b):
    try:
        a = float(a)
    except (TypeError, ValueError):
        pass
    try:
        b = float(b)
    except (TypeError, ValueError):
        pass
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        res = a + b
        return int(res) if isinstance(res, float) and res.is_integer() else res
    return str(a) + str(b)