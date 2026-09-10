def solve_task(a, b):
    try:
        a = float(a) if isinstance(a, str) and a.replace('.', '', 1).isdigit() else a
    except ValueError:
        pass
    try:
        b = float(b) if isinstance(b, str) and b.replace('.', '', 1).isdigit() else b
    except ValueError:
        pass
    try:
        return a + b
    except TypeError:
        return str(a) + str(b)