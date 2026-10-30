#!/usr/bin/env python3
"""Plot recorded legal flips and an explicitly verified heptagon fan sweep.

Verification scripts use the standard library. This optional plotting script
requires matplotlib; it writes PDF, EPS and PNG files to --out-dir.
"""
import argparse
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from verify_fan_endpoints import analyze, trace


def panel(ax, state, N, title, footer, special=None, centre=None):
    xy = [(math.cos(math.pi/2-2*math.pi*k/N),
           math.sin(math.pi/2-2*math.pi*k/N)) for k in range(N)]
    owners, legal = analyze(state)
    edges = set()
    for tri, value in state.items():
        pts = [xy[v] for v in tri]
        ax.add_patch(Polygon(pts, facecolor='#e0eff5' if value > 0 else '#f5e7d4',
                             edgecolor='none'))
        x, y = (sum(p[k] for p in pts)/3 for k in (0, 1))
        ax.text(x, y, '+' if value > 0 else '$-$', ha='center', va='center',
                fontsize=14)
        for k in range(3):
            edges.add(tuple(sorted((tri[k], tri[(k+1) % 3]))))
    for e in sorted(edges):
        color, width, style = '#69717c', 1.0, '-'
        if e in legal:
            color, width = '#b14324', 2.0
        if e == special:
            color, width, style = '#075f80', 2.5, '-' if e in legal else '--'
        ax.plot([xy[v][0] for v in e], [xy[v][1] for v in e],
                color=color, linewidth=width, linestyle=style)
    for k, point in enumerate(xy):
        ax.scatter(*point, c='#075f80' if k == centre else '#202830',
                   s=38 if k == centre else 13, zorder=5)
        ax.text(point[0]*1.16, point[1]*1.16, str(k), ha='center', va='center',
                fontsize=11, fontweight='bold' if k == centre else 'normal')
    ax.set_title(title, fontsize=11, pad=8)
    ax.text(0, -1.42, footer, ha='center', va='center', fontsize=10,
            color='#075f80')
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.6, 1.3)
    ax.set_aspect('equal')
    ax.axis('off')


def save(fig, out, name, wspace=.15):
    fig.subplots_adjust(left=.02, right=.98, bottom=.03, top=.88, wspace=wspace)
    for ext in ('pdf', 'eps', 'png'):
        fig.savefig(out / (name + '.' + ext), bbox_inches='tight', dpi=180)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--results', type=Path, default=Path('results/fan_endpoint_results.json'))
    p.add_argument('--out-dir', type=Path, default=Path('figures'))
    args = p.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    snapshots = json.loads(args.results.read_text())['forbidden_turn']['snapshots']
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9))
    titles = ['After removing 02', 'After removing 03', 'After turning to 35']
    footers = ['13 is the inverse move', '13 is blocked', '13 becomes legal again']
    for j, (ax, snap) in enumerate(zip(axes, snapshots)):
        state = {tuple(t['vertices']): t['sign'] for t in snap['triangles']}
        assert analyze(state)[1] == {tuple(e) for e in snap['legal_diagonals']}
        panel(ax, state, 6, titles[j], footers[j], special=(1, 3))
    save(fig, args.out_dir, 'forbidden_turn')

    N = 7
    initial = {(0, k, k+1): (1 if k == 1 else (-1)**k) for k in range(1, N-1)}
    status, route, states = trace(initial, N, audit=True)
    assert status == 'minimum_path' and len(states) == 5
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9))
    for ax, j, title, footer, hub in zip(
            axes, (0, 2, 4), ('Endpoint', 'Middle state', 'Endpoint'),
            ('Fan centre 0', 'Two legal moves', 'Fan centre 1'), (0, None, 1)):
        panel(ax, states[j], N, title, footer, centre=hub)
    fig.subplots_adjust(left=.02, right=.98, bottom=.03, top=.88, wspace=.40)
    gaps = [(axes[j].get_position().x1 + axes[j+1].get_position().x0)/2
            for j in (0, 1)]
    for x in gaps:
        fig.text(x, .47, r'$\longrightarrow$', ha='center', fontsize=16)
        fig.text(x, .40, '2 flips', ha='center', fontsize=9)
    save(fig, args.out_dir, 'fan_sweep', wspace=.40)


if __name__ == '__main__':
    main()
