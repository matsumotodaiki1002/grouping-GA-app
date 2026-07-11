import unittest

from ga import calculate_score, run_ga


class GATest(unittest.TestCase):
    def test_score_counts_each_pair_once(self):
        matrix = [[0, 3, -1, 0], [3, 0, 0, 0], [-1, 0, 0, 5], [0, 0, 5, 0]]
        self.assertEqual(calculate_score([0, 1, 2, 3], matrix, 2), 8)

    def test_result_respects_group_sizes(self):
        matrix = [[0 if i == j else 1 for j in range(6)] for i in range(6)]
        result = run_ga(matrix, 2, 3, population_size=12, generations=5, seed=1)
        self.assertEqual([len(group) for group in result.groups], [3, 3])
        self.assertEqual(sorted(member for group in result.groups for member in group), list(range(6)))

    def test_seed_is_reproducible(self):
        matrix = [[0 if i == j else i + j for j in range(6)] for i in range(6)]
        one = run_ga(matrix, 2, 3, population_size=12, generations=5, seed=7)
        two = run_ga(matrix, 2, 3, population_size=12, generations=5, seed=7)
        self.assertEqual(one, two)


if __name__ == "__main__":
    unittest.main()
