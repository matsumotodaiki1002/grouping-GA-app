"""班分け用の遺伝的アルゴリズム。UIに依存しない純粋なロジック。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class GAResult:
    groups: list[list[int]]
    score: float
    generations: int


def balanced_group_sizes(member_count: int, group_count: int) -> list[int]:
    """端数を後ろの班に割り当てる。11名・3班なら3, 4, 4。"""
    if group_count < 1 or group_count > member_count:
        raise ValueError("班数は1以上、参加者数以下にしてください。")
    base, remainder = divmod(member_count, group_count)
    return [base] * (group_count - remainder) + [base + 1] * remainder


def _resolve_group_sizes(member_count: int, group_size: int | list[int]) -> list[int]:
    if isinstance(group_size, int):
        if group_size < 1 or member_count % group_size:
            raise ValueError("班の人数の合計を参加者数と一致させてください。")
        sizes = [group_size] * (member_count // group_size)
    else:
        sizes = list(group_size)
    if not sizes or any(type(size) is not int or size < 1 for size in sizes):
        raise ValueError("各班の人数は1以上の整数にしてください。")
    if sum(sizes) != member_count:
        raise ValueError("班の人数の合計を参加者数と一致させてください。")
    return sizes


def _split_groups(order: list[int], sizes: list[int]) -> list[list[int]]:
    groups = []
    start = 0
    for size in sizes:
        groups.append(order[start : start + size])
        start += size
    return groups


def calculate_score(order: list[int], matrix: list[list[float]], group_size: int | list[int]) -> float:
    sizes = _resolve_group_sizes(len(order), group_size)
    score = 0.0
    for group in _split_groups(order, sizes):
        for left, right in combinations(group, 2):
            score += matrix[left][right]
    return score


def _ordered_crossover(parent1: list[int], parent2: list[int], rng: random.Random) -> list[int]:
    """順列を壊さない順序交叉（OX）。"""
    size = len(parent1)
    left, right = sorted(rng.sample(range(size), 2))
    child: list[int | None] = [None] * size
    child[left : right + 1] = parent1[left : right + 1]
    remaining = [member for member in parent2 if member not in child]
    positions = list(range(right + 1, size)) + list(range(0, left))
    for position, member in zip(positions, remaining):
        child[position] = member
    return [int(member) for member in child]


def _mutate(order: list[int], mutation_rate: float, rng: random.Random) -> None:
    if rng.random() < mutation_rate:
        left, right = rng.sample(range(len(order)), 2)
        order[left], order[right] = order[right], order[left]


def _tournament(population: list[list[int]], scores: list[float], rng: random.Random) -> list[int]:
    candidates = rng.sample(range(len(population)), min(4, len(population)))
    return population[max(candidates, key=lambda index: scores[index])]


def run_ga(
    matrix: list[list[float]],
    group_count: int,
    group_size: int | None = None,
    *,
    group_sizes: list[int] | None = None,
    population_size: int = 80,
    generations: int = 180,
    mutation_rate: float = 0.2,
    seed: int | None = None,
) -> GAResult:
    member_count = len(matrix)
    if member_count < 2:
        raise ValueError("参加者は2名以上必要です。")
    if group_sizes is not None:
        sizes = _resolve_group_sizes(member_count, group_sizes)
    elif group_size is not None:
        sizes = _resolve_group_sizes(member_count, group_size)
    else:
        sizes = balanced_group_sizes(member_count, group_count)
    if len(sizes) != group_count:
        raise ValueError("指定した班の人数は、班数と同じ個数にしてください。")
    if population_size < 4 or generations < 1:
        raise ValueError("GAの実行条件が不正です。")

    rng = random.Random(seed)
    base = list(range(member_count))
    population: list[list[int]] = []
    for _ in range(population_size):
        individual = base.copy()
        rng.shuffle(individual)
        population.append(individual)

    best = population[0].copy()
    best_score = calculate_score(best, matrix, sizes)

    for _ in range(generations):
        scores = [calculate_score(individual, matrix, sizes) for individual in population]
        elite_index = max(range(len(population)), key=scores.__getitem__)
        if scores[elite_index] > best_score:
            best, best_score = population[elite_index].copy(), scores[elite_index]

        next_population = [population[elite_index].copy()]
        while len(next_population) < population_size:
            parent1 = _tournament(population, scores, rng)
            parent2 = _tournament(population, scores, rng)
            child = _ordered_crossover(parent1, parent2, rng)
            _mutate(child, mutation_rate, rng)
            next_population.append(child)
        population = next_population

    groups = _split_groups(best, sizes)
    return GAResult(groups=groups, score=best_score, generations=generations)
