def solve_task(a, b):
    try:
        a = float(a)
    except (TypeError, ValueError):
        pass
    try:
        b = float(b)
    except (TypeError, ValueError):
        pass
    res = a + b
    if isinstance(res, float) and res.is_integer():
        return int(res)
    return res