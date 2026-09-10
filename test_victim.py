import unittest
from victim import solve_task

class TestVictim(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(solve_task(2, 3), 5)
        self.assertEqual(solve_task(-1, 1), 0)
        self.assertEqual(solve_task(0, 0), 0)

if __name__ == '__main__':
    unittest.main()
