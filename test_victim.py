import unittest
from victim import solve_task

class TestVictim(unittest.TestCase):
    def test_integers(self):
        self.assertEqual(solve_task(2, 3), 5)
        self.assertEqual(solve_task(-1, 1), 0)

    def test_string_numbers(self):
        self.assertEqual(solve_task("10", "20"), 30)
        self.assertEqual(solve_task("5", 5), 10)

    def test_invalid_input(self):
        # Если передан мусор вместо числа — ОБЯЗАН выбросить ValueError
        with self.assertRaises(ValueError):
            solve_task("abc", 5)

if __name__ == '__main__':
    unittest.main()
