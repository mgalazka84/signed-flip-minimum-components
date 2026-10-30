#!/usr/bin/env python3
"""Exhaustive signed-flip verification; standard library only.

Vertices are labelled 0,...,N-1 counterclockwise. Triangle bit 1 denotes +.
All triangulations, all signings and all legal flips are generated directly.
No theorem about component connectivity is used to build the graph.
"""
import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, permutations
from pathlib import Path


def sign(x, y, z):
    edges = (x ^ y, y ^ z, z ^ x)
    assert set(edges) == {1, 2, 3}
    return int(edges in ((1, 2, 3), (2, 3, 1), (3, 1, 2)))


@lru_cache(None)
def triangulations(lo, hi):
    if hi - lo < 2:
        return ((),)
    return tuple(tuple(sorted(left + right + ((lo, k, hi),)))
                 for k in range(lo + 1, hi)
                 for left in triangulations(lo, k)
                 for right in triangulations(k, hi))


def colour_plan(tris):
    """Root on boundary edge (0,1); each step introduces one new vertex."""
    known = {0, 1}
    pending = list(enumerate(tris))
    plan = []
    while pending:
        for idx, (j, t) in enumerate(pending):
            unknown = set(t) - known
            if len(unknown) == 1:
                v = unknown.pop()
                plan.append((j, t, v))
                known.add(v)
                pending.pop(idx)
                break
        else:
            raise AssertionError('No dual-tree traversal step')
    return plan


COLOUR = {}
for vpos in range(3):
    for a, b in permutations(range(4), 2):
        for c in range(4):
            if c not in (a, b):
                t = [a, b]
                t.insert(vpos, c)
                COLOUR[vpos, a, b, sign(*t)] = c


def colour_code(plan, mask, N):
    cols = [-1] * N
    cols[0], cols[1] = 0, 1
    for j, t, v in plan:
        pos = t.index(v)
        a, b = [cols[w] for w in t if w != v]
        cols[v] = COLOUR[pos, a, b, (mask >> j) & 1]
    return sum(c << (2 * i) for i, c in enumerate(cols))


def count_compatible(cols):
    """Independent interval DP counting properly coloured triangulations."""
    N = len(cols)
    dp = [[0] * N for _ in range(N)]
    for i in range(N - 1):
        dp[i][i + 1] = int(cols[i] != cols[i + 1])
    for width in range(2, N):
        for i in range(N - width):
            j = i + width
            if cols[i] == cols[j]:
                continue
            dp[i][j] = sum(dp[i][k] * dp[k][j]
                           for k in range(i + 1, j)
                           if len({cols[i], cols[k], cols[j]}) == 3)
    return dp[0][N - 1]


def local_check():
    for p in permutations(range(4)):
        inversions = sum(p[i] > p[j] for i in range(4) for j in range(i+1, 4))
        assert (2 * sign(*p[:3]) - 1) == -((-1) ** inversions)
    # All proper colourings of triangles abc, acd; not only four distinct colours.
    count = 0
    for a in range(4):
        for b in range(4):
            for c in range(4):
                for d in range(4):
                    if len({a, b, c}) != 3 or len({a, c, d}) != 3:
                        continue
                    s1, s2 = sign(a, b, c), sign(a, c, d)
                    assert (s1 == s2) == (b != d)
                    if s1 == s2:
                        assert sign(a, b, d) == sign(b, c, d) == 1 - s1
                    count += 1
    assert count == 48
    return count


def verify(N):
    started = time.perf_counter()
    ts = triangulations(0, N - 1)
    n = N - 2
    assert len(ts) == math.comb(2 * n, n) // (n + 1)
    assert len(set(ts)) == len(ts)
    index = {t: i for i, t in enumerate(ts)}
    M = 1 << n
    size = len(ts) * M
    parent = list(range(size))
    weight = [1] * size
    degree = [0] * size
    codes = [0] * size
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            if weight[a] < weight[b]:
                a, b = b, a
            parent[b] = a
            weight[a] += weight[b]
    for ti, t in enumerate(ts):
        plan = colour_plan(t)
        for mask in range(M):
            code = colour_code(plan, mask, N)
            codes[ti * M + mask] = code
            for j, (a, b, c) in enumerate(t):
                assert sign((code >> (2*a)) & 3,
                            (code >> (2*b)) & 3,
                            (code >> (2*c)) & 3) == ((mask >> j) & 1)
    edges = 0
    for ti, t in enumerate(ts):
        owners = defaultdict(list)
        for j, tri in enumerate(t):
            for e in combinations(tri, 2):
                owners[e].append(j)
        for js in owners.values():
            if len(js) != 2:
                continue
            a, b = js
            vertices = sorted(set(t[a]) | set(t[b]))
            newtris = tuple(x for x in combinations(vertices, 3)
                            if x not in (t[a], t[b]))
            tt = tuple(sorted(tuple(x for j, x in enumerate(t)
                                    if j not in (a, b)) + newtris))
            tj = index[tt]
            if tj <= ti:
                continue
            unchanged = [(i, tt.index(tri)) for i, tri in enumerate(t)
                         if i not in (a, b)]
            newbitmask = sum(1 << tt.index(tri) for tri in newtris)
            for mask in range(M):
                s = (mask >> a) & 1
                if s != ((mask >> b) & 1):
                    continue
                target = sum(((mask >> i) & 1) << j for i, j in unchanged)
                if not s:
                    target |= newbitmask
                u, v = ti * M + mask, tj * M + target
                assert codes[u] == codes[v], (N, t, mask, tt, target)
                union(u, v)
                degree[u] += 1
                degree[v] += 1
                edges += 1
    expected_edges = len(ts) * (N - 3) * M // 4 if N > 3 else 0
    assert edges == expected_edges
    roots = [find(i) for i in range(size)]
    hist = Counter(Counter(roots).values())
    # Independently compare signs of every recurring triangle within each component.
    triangle_signs = {}
    for ti, t in enumerate(ts):
        for mask in range(M):
            r = roots[ti * M + mask]
            for j, tri in enumerate(t):
                key, s = (r, tri), (mask >> j) & 1
                if key in triangle_signs:
                    assert triangle_signs[key] == s
                else:
                    triangle_signs[key] = s
    # Verify that each four-colour fibre is one component, and DP gives its size.
    fibres = defaultdict(Counter)
    for u, code in enumerate(codes):
        fibres[code][roots[u]] += 1
    four_fibres = 0
    for code, components in fibres.items():
        cols = tuple((code >> (2*i)) & 3 for i in range(N))
        total = sum(components.values())
        assert count_compatible(cols) == total
        if len(set(cols)) == 4:
            assert len(components) == 1
            four_fibres += 1
        else:
            assert set(components.values()) == {1}
    predicted_nontrivial = (3**N - 4 * 2**N + 6 + (-1)**N) // 12
    assert four_fibres == predicted_nontrivial
    assert hist[1] == 2 * len(ts)
    assert sum(hist.values()) == 2 * len(ts) + predicted_nontrivial
    minimum = min((k for k in hist if k > 1), default=None)
    minimal_roots = {r for r in set(roots) if minimum and weight[r] == minimum}
    minimal_max_degree = max((degree[u] for u in range(size)
                              if roots[u] in minimal_roots), default=0)
    minimum_degree_profiles = defaultdict(Counter)
    for u, r in enumerate(roots):
        if r in minimal_roots:
            minimum_degree_profiles[r][degree[u]] += 1
    expected_path_profile = Counter({1: 2})
    if minimum and minimum > 2:
        expected_path_profile[2] = minimum - 2
    all_minimum_are_paths = (all(x == expected_path_profile
                               for x in minimum_degree_profiles.values())
                             if minimum else None)
    result = dict(polygon_vertices=N, triangles=n, triangulations=len(ts),
                  signed_states=size, undirected_edges=edges,
                  components=sum(hist.values()), isolated_components=hist[1],
                  four_colour_fibres=four_fibres,
                  minimum_nontrivial_size=minimum,
                  minimum_nontrivial_count=len(minimal_roots),
                  minimum_components_max_degree=minimal_max_degree,
                  all_minimum_components_are_paths=all_minimum_are_paths,
                  component_size_histogram=dict(sorted(hist.items())),
                  all_checks_passed=True,
                  seconds=round(time.perf_counter() - started, 3))
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-n', type=int, default=10,
                        help='maximum number of polygon vertices')
    parser.add_argument('--out', default='results.json')
    args = parser.parse_args()
    rows = []
    hexagon_word = (0, 1, 0, 2, 0, 3)
    hexagon_ts = [t for t in triangulations(0, 5)
                  if all(len({hexagon_word[v] for v in tri}) == 3 for tri in t)]
    hexagon_edges = [(i, j) for i in range(len(hexagon_ts)) for j in range(i)
                     if len(set(hexagon_ts[i]) - set(hexagon_ts[j])) == 2]
    hexagon_degrees = [sum(i in e for e in hexagon_edges) for i in range(len(hexagon_ts))]
    assert count_compatible(hexagon_word) == len(hexagon_ts) == 4
    assert sorted(hexagon_degrees) == [1, 1, 1, 3]
    report = dict(local_quadrilateral_checks=local_check(),
                  hexagon_star_example=dict(colour_word=hexagon_word,
                      triangulations=hexagon_ts, edges=hexagon_edges,
                      degrees=hexagon_degrees), rows=rows)
    for N in range(3, args.max_n + 1):
        rows.append(verify(N))
        Path(args.out).write_text(json.dumps(report, indent=2) + '\n')
    fields = [k for k in rows[0] if k != 'component_size_histogram']
    with Path(args.out).with_suffix('.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in rows)


if __name__ == '__main__':
    main()
