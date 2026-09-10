def solve_task(a, b):
    try:
        val_a = float(a)
        val_b = float(b)
        res = val_a + val_b
        return int(res) if res.is_integer() else res
    except (TypeError, ValueError):
        return str(a) + str(b)