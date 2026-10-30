#!/usr/bin/env python3
"""Exhaustively test the fan-endpoint criterion, without assuming monotonicity.

Enumerate every triangulation and every signing with exactly one legal move,
up to global sign reversal. Follow the actual signed flips until reaching an
endpoint, a branching state, a repeated state, or exceeding the minimum size.
This is finite verification, not the general proof.

Python 3.10+, standard library only. No randomness or floating-point counts.
"""
import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations
from pathlib import Path


@lru_cache(None)
def triangulations(i, j):
    if j - i < 2:
        return ((),)
    return tuple(tuple(sorted(a + b + ((i, k, j),)))
                 for k in range(i + 1, j)
                 for a in triangulations(i, k)
                 for b in triangulations(k, j))


def analyze(state):
    owners = defaultdict(list)
    for tri in state:
        for edge in combinations(tri, 2):
            owners[edge].append(tri)
    internal = {e: t for e, t in owners.items() if len(t) == 2}
    legal = {e for e, (a, b) in internal.items() if state[a] == state[b]}
    return internal, legal


def flip(state, edge, owners):
    a, b = owners[edge]
    assert state[a] == state[b]
    quad = sorted(set(a) | set(b))
    new_triangles = [t for t in combinations(quad, 3) if t not in (a, b)]
    new_edge = tuple(sorted(set(quad) - set(edge)))
    value = -state[a]
    out = {t: s for t, s in state.items() if t not in (a, b)}
    out.update({t: value for t in new_triangles})
    return out, new_edge


def endpoint_signing(tris, equal_edge, owners):
    dual = defaultdict(list)
    for edge, (a, b) in owners.items():
        dual[a].append((b, edge))
        dual[b].append((a, edge))
    state = {tris[0]: 1}
    stack = [tris[0]]
    while stack:
        a = stack.pop()
        for b, edge in dual[a]:
            if b not in state:
                state[b] = state[a] if edge == equal_edge else -state[a]
                stack.append(b)
    assert len(state) == len(tris)
    return state


def key(state):
    return tuple(sorted(state.items()))


def trace(state, N, audit=False):
    """Classify by actual moves, without restricting which diagonal is removed."""
    seen = {key(state)}
    previous = None
    route, states = [], [state]
    while True:
        owners, legal = analyze(state)
        options = legal - ({previous} if previous else set())
        if not options:
            status = 'minimum_path' if len(states) == N - 2 else 'other_path'
            return status, route, states
        if len(options) != 1:
            return 'branching', route, states
        if len(states) >= N - 2:
            return 'exceeds_minimum', route, states
        edge = next(iter(options))
        target, inserted = flip(state, edge, owners)
        if audit:
            pair = owners[edge]
            sides = set(combinations(pair[0], 2)) ^ set(combinations(pair[1], 2))
            internal_sides = sides & set(owners)
            expected = ((legal - {edge}) ^ internal_sides) | {inserted}
            assert analyze(target)[1] == expected
        route.append((edge, inserted))
        if key(target) in seen:
            return 'cycle', route, states
        seen.add(key(target))
        states.append(target)
        state, previous = target, inserted


def fan_data(tris, owners):
    hubs = set.intersection(*(set(e) for e in owners))
    degree = Counter(t for pair in owners.values() for t in pair)
    terminal_edges = {e for e, pair in owners.items()
                      if any(degree[t] == 1 for t in pair)}
    return hubs, terminal_edges


def verify(N):
    started = time.perf_counter()
    ts = triangulations(0, N - 1)
    assert len(ts) == math.comb(2 * (N - 2), N - 2) // (N - 1)
    hist = Counter()
    for tris in ts:
        owners, _ = analyze(dict.fromkeys(tris, 1))
        hubs, terminal_edges = fan_data(tris, owners)
        for equal_edge in owners:
            state = endpoint_signing(tris, equal_edge, owners)
            assert analyze(state)[1] == {equal_edge}
            status, route, states = trace(state, N, audit=(N <= 9))
            hist[status] += 1
            expected = bool(hubs) and equal_edge in terminal_edges
            assert (status == 'minimum_path') == expected, (N, tris, equal_edge)
            if status == 'minimum_path':
                original = set(owners)
                removed = [e for e, f in route]
                inserted = [f for e, f in route]
                assert len(removed) == len(set(removed)) == N - 3
                assert set(removed) == original
                assert not (set(inserted) & original)
                assert len(set(inserted)) == N - 3
                for j, current in enumerate(states):
                    ds, legal = analyze(current)
                    assert set(inserted[:j]) <= set(ds)
                    assert not (set(inserted[:max(0, j - 1)]) & legal)
                other_owners, _ = analyze(states[-1])
                other_hubs, _ = fan_data(tuple(states[-1]), other_owners)
                assert len(hubs) == len(other_hubs) == 1
                u, v = next(iter(hubs)), next(iter(other_hubs))
                assert (u - v) % N in (1, N - 1)
    candidates = len(ts) * (N - 3)
    assert sum(hist.values()) == candidates
    assert hist['minimum_path'] == 2 * N
    return dict(polygon_vertices=N, triangulations=len(ts),
                endpoint_candidates_up_to_global_sign=candidates,
                traversal_outcomes=dict(sorted(hist.items())),
                signed_minimum_path_endpoints=2 * hist['minimum_path'],
                minimum_path_components=hist['minimum_path'],
                all_checks_passed=True,
                elapsed_seconds=round(time.perf_counter() - started, 3))


def large_fan_checks(max_N=40):
    for N in range(5, max_N + 1):
        tris = tuple((0, k, k + 1) for k in range(1, N - 1))
        state = {t: (1 if k == 1 else (-1) ** k)
                 for k, t in enumerate(tris, 1)}
        status, route, states = trace(state, N, audit=True)
        assert status == 'minimum_path'
        assert route == [((0, j + 1), (1, j + 2)) for j in range(1, N - 2)]
        assert all(states[j][(0, 1, j + 2)] == (-1) ** j for j in range(N - 2))
    return dict(min_N=5, max_N=max_N, all_checks_passed=True)


def turn_certificate():
    state = {(0, 1, 2): 1, (0, 2, 3): 1, (0, 3, 5): -1, (3, 4, 5): 1}
    snapshots = []
    for edge in [(0, 2), (0, 3), (3, 5)]:
        owners, legal = analyze(state)
        assert edge in legal
        state, inserted = flip(state, edge, owners)
        snapshots.append(dict(removed=list(edge), inserted=list(inserted),
                              triangles=[dict(vertices=list(t), sign=s)
                                         for t, s in sorted(state.items())],
                              legal_diagonals=[list(e) for e in sorted(analyze(state)[1])]))
    assert (1, 3) not in {tuple(e) for e in snapshots[1]['legal_diagonals']}
    assert (1, 3) in analyze(state)[1]
    return dict(polygon_vertices=6, snapshots=snapshots,
                revived_inserted_diagonal=[1, 3], all_checks_passed=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-n', type=int, default=12)
    parser.add_argument('--out', type=Path, default=Path('fan_endpoint_results.json'))
    args = parser.parse_args()
    rows = []
    for N in range(5, args.max_n + 1):
        row = verify(N)
        rows.append(row)
        print(json.dumps(row), flush=True)
    report = dict(method='Exhaustive degree-one states, modulo global sign reversal; direct legal-move traversal',
                  dependency_on_general_proof=False,
                  finite_evidence_only=True,
                  summary=rows,
                  explicit_fan_sweeps=large_fan_checks(),
                  forbidden_turn=turn_certificate())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    fields = ['polygon_vertices', 'triangulations',
              'endpoint_candidates_up_to_global_sign',
              'signed_minimum_path_endpoints', 'minimum_path_components',
              'all_checks_passed', 'elapsed_seconds']
    with args.out.with_suffix('.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in rows)


if __name__ == '__main__':
    main()
