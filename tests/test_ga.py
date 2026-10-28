import unittest

from ga import balanced_group_sizes, calculate_score, run_ga


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

    def test_eleven_people_are_split_without_losing_or_duplicating_members(self):
        matrix = [[0 if i == j else i + j for j in range(11)] for i in range(11)]
        for sizes in ([3, 4, 4], [2, 4, 5], [1, 10]):
            with self.subTest(sizes=sizes):
                result = run_ga(matrix, len(sizes), group_sizes=sizes, population_size=12, generations=8, seed=19)
                self.assertEqual([len(group) for group in result.groups], sizes)
                self.assertEqual(sorted(member for group in result.groups for member in group), list(range(11)))
                manual_score = sum(matrix[left][right] for group in result.groups for i, left in enumerate(group) for right in group[i + 1:])
                self.assertEqual(result.score, manual_score)

    def test_balanced_allocation_handles_remainders(self):
        self.assertEqual(balanced_group_sizes(11, 3), [3, 4, 4])
        self.assertEqual(balanced_group_sizes(12, 3), [4, 4, 4])
        self.assertEqual(balanced_group_sizes(2, 2), [1, 1])

    def test_rejects_invalid_sizes(self):
        matrix = [[0] * 11 for _ in range(11)]
        for sizes in ([3, 3, 4], [0, 5, 6], [-1, 6, 6], [3.5, 3.5, 4], [5, 6]):
            with self.subTest(sizes=sizes), self.assertRaises(ValueError):
                run_ga(matrix, 3, group_sizes=sizes)

    def test_variable_size_score_uses_correct_group_boundaries(self):
        matrix = [[0, 100, 100, 100], [100, 0, 2, 3], [100, 2, 0, 5], [100, 3, 5, 0]]
        self.assertEqual(calculate_score([0, 1, 2, 3], matrix, [1, 3]), 10)


if __name__ == "__main__":
    unittest.main()
