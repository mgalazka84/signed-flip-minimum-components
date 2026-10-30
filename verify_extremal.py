#!/usr/bin/env python3
"""Independent boundary-word enumeration and local proof certificates.

Python 3.10+, standard library only. No random choices or floating point counts.
The direct signed-state enumeration is in verify_flips.py; this program instead
enumerates normalized proper boundary words and uses interval dynamic programming.
Finite checks of the 2N count are evidence, not a proof for arbitrary N.
"""
import argparse
import csv
import json
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from verify_flips import count_compatible, sign


def words(N):
    a = [0, 1]
    def visit():
        if len(a) == N:
            if a[-1] != 0 and len(set(a)) == 4:
                yield tuple(a)
            return
        for c in range(4):
            if c != a[-1]:
                a.append(c)
                yield from visit()
                a.pop()
    yield from visit()


def compatible(c):
    @lru_cache(None)
    def rec(i, j):
        if c[i] == c[j]:
            return ()
        if j == i + 1:
            return ((),)
        return tuple(tuple(sorted(a + b + ((i, k, j),)))
                     for k in range(i + 1, j)
                     if len({c[i], c[k], c[j]}) == 3
                     for a in rec(i, k) for b in rec(k, j))
    return rec(0, len(c) - 1)


def diagonals(t, N):
    return frozenset(e for tri in t for e in combinations(tri, 2)
                     if e[1] != e[0] + 1 and e != (0, N - 1))


def adjacency(ts, N):
    ds = [diagonals(t, N) for t in ts]
    adj = [[] for _ in ts]
    for i in range(len(ts)):
        for j in range(i):
            if len(ds[i] - ds[j]) == len(ds[j] - ds[i]) == 1:
                adj[i].append(j)
                adj[j].append(i)
    return ds, adj


def canonical(c):
    def rename(a):
        m = {}
        return tuple(m.setdefault(x, len(m)) for x in a)
    return min(rename(a[k:] + a[:k])
               for a in (c, c[::-1]) for k in range(len(c)))


def check_minimum(c):
    N = len(c)
    ts = compatible(c)
    assert len(ts) == N - 2
    ds, adj = adjacency(ts, N)
    assert sum(map(len, adj)) == 2 * (len(ts) - 1)
    # Check the spanning-tree conclusion for EVERY choice of root.
    for root in range(len(ts)):
        q = deque([root])
        dist = {root: 0}
        labels = []
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v in dist:
                    continue
                removed = (ds[u] - ds[v]) & ds[root]
                assert len(removed) == 1
                assert not ((ds[v] - ds[u]) & ds[root])
                labels.extend(removed)
                dist[v] = dist[u] + 1
                q.append(v)
        assert len(dist) == len(ts)
        assert len(labels) == len(set(labels)) == N - 3
        assert set(labels) == set(ds[root])
        for v in dist:
            assert dist[v] == len(ds[root] - ds[v])
    profile = Counter(map(len, adj))
    is_path = profile == Counter({1: 2, 2: N - 4}) if N > 4 else profile == {1: 2}
    if N >= 7:
        assert is_path
    return 'path' if is_path else 'star', ts, adj


def flip_signed(state, diagonal):
    owners = [t for t in state if set(diagonal) <= set(t)]
    assert len(owners) == 2
    s = state[owners[0]]
    assert state[owners[1]] == s
    quad = sorted(set(owners[0]) | set(owners[1]))
    new = [t for t in combinations(quad, 3) if t not in owners]
    out = {t: v for t, v in state.items() if t not in owners}
    out.update({t: -s for t in new})
    return out


def local_certificate():
    initial = {(0, 1, 2): 1, (0, 2, 4): 1, (2, 3, 4): 1,
               (0, 4, 6): 1, (4, 5, 6): -1}
    route = [(0, 4), (4, 6), (2, 4)]
    states = [initial]
    for e in route:
        states.append(flip_signed(states[-1], e))
    direct = flip_signed(initial, (2, 4))
    assert (2, 4) in diagonals(tuple(states[2]), 7)
    assert (2, 4) not in diagonals(tuple(states[3]), 7)
    assert initial != states[2] and direct != states[3]
    # The two distinct edges both remove original diagonal 24.
    def encode(s):
        return [{'triangle': list(t), 'sign': v} for t, v in sorted(s.items())]
    return dict(polygon_vertices=7, route=[list(e) for e in route],
                states=[encode(s) for s in states], direct_flip=[2, 4],
                direct_target=encode(direct), repeated_original_diagonal=[2, 4],
                all_checks_passed=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--max-n', type=int, default=12)
    p.add_argument('--out-dir', type=Path, default=Path('results'))
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows, examples = [], []
    for N in range(4, args.max_n + 1):
        hist, minimizers = Counter(), []
        for c in words(N):
            s = count_compatible(c)
            assert s >= N - 2
            hist[s] += 1
            if s == N - 2:
                minimizers.append(c)
        expected = (3**N - 4 * 2**N + 6 + (-1)**N) // 12
        assert sum(hist.values()) == expected
        shapes = Counter()
        types = Counter(canonical(c) for c in minimizers)
        for c in minimizers:
            shape, ts, adj = check_minimum(c)
            shapes[shape] += 1
        if N >= 7:
            assert len(minimizers) == 2 * N
            assert len(types) == 1
        row = dict(polygon_vertices=N, normalized_four_colour_words=sum(hist.values()),
                   minimum_size=min(hist), minimum_count=len(minimizers),
                   path_count=shapes['path'], star_count=shapes['star'],
                   canonical_types=len(types), all_checks_passed=True)
        rows.append(row)
        examples.append(dict(polygon_vertices=N,
                             canonical_words=[dict(word=list(c), count=n)
                                              for c, n in sorted(types.items())],
                             minimum_words=[list(c) for c in minimizers],
                             size_histogram=dict(sorted(hist.items()))))
        print(json.dumps(row), flush=True)
    (args.out_dir / 'boundary_results.json').write_text(
        json.dumps({'summary': rows, 'details': examples}, indent=2) + '\n')
    with (args.out_dir / 'boundary_results.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    (args.out_dir / 'local_certificate.json').write_text(
        json.dumps(local_certificate(), indent=2) + '\n')


if __name__ == '__main__':
    main()
