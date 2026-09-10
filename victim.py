def solve_task(a, b):
    try:
        def parse(val):
            if isinstance(val, str):
                val = val.strip()
                if not val:
                    raise ValueError()
            return float(val)

        res = parse(a) + parse(b)
        return int(res) if res.is_integer() else res
    except (TypeError, ValueError):
        raise ValueError("Invalid input: arguments must be numeric or convertible to numeric")