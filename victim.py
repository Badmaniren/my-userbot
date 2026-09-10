def solve_task(a, b):
    try:
        res = float(a) + float(b)
        return int(res) if res.is_integer() else res
    except (TypeError, ValueError):
        raise ValueError("Invalid input: arguments must be numeric or convertible to numeric")