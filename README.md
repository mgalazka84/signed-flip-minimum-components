# Signed flip computations

Reproducible code and numerical results for signed triangulations of convex
polygons. This repository contains no manuscript, manuscript source, cover
letter, or submission material.

## Reproduce

Python 3.10 or newer; no third-party packages are required.
Run from the repository root:

```sh
python3 verify_flips.py --max-n 10 --out results/signed_results.json
python3 verify_extremal.py --max-n 12 --out-dir results
python3 verify_fan_endpoints.py --max-n 12 --out results/fan_endpoint_results.json
```

All verification scripts stop with an assertion error on a failed check. Do not run them
with `python -O`, which disables assertions. Counts are deterministic; the
timing fields in the signed-state and fan-endpoint results depend on the machine.

## Conventions

- `N` is the number of labelled polygon vertices, listed counterclockwise.
- There are `N-2` triangles and `N-3` internal diagonals.
- A flip is legal when its two triangle signs agree; both new signs reverse.
- Rotations, reflections and global sign reversal are not identified.
- Boundary colours are 0, 1, 2, 3, with the first two fixed to 0, 1.
- In `verify_flips.py`, bit 1 means positive. The local certificate uses +1/-1.

## Files and independent checks

`verify_flips.py` constructs the complete signed-state graph directly. It
checks local colour identities, sign reconstruction and invariance, every
recurring triangle sign, connected components, degree profiles and an
independent interval recurrence. The checked range N=3,...,10 contains
431,058 states and 735,102 undirected edges.

`verify_extremal.py` independently enumerates proper normalized four-colour
boundary words, counts compatible triangulations by interval dynamic
programming, and explicitly builds each graph that attains N-2 states.
For each such graph and every root it checks the tree property, unique
root-diagonal changes and the exact diagonal-distance identity. It also
checks a three-flip local certificate, saved as `results/local_certificate.json`.

`results/signed_results.json` and `.csv` contain complete signed-graph counts
through N=10. `results/boundary_results.json` contains word counts, size
histograms and all minimum words through N=12; its CSV is the compact summary.

`verify_fan_endpoints.py` separately generates every triangulation and every
signing with one legal move, up to global sign reversal. It follows actual
legal moves without requiring removal of original diagonals. Across 203,524
candidates for N=5,...,12 it checks that a minimum path endpoint is exactly
a signed fan with one terminal equal-sign pair. It checks the permanence of
inserted diagonals and the adjacent fan centres of accepted paths. Explicit
fan sweeps are checked through N=40. The JSON records all outcomes and the
forbidden-turn certificate; the CSV provides a summary. The coefficient
`4*N` counts signed endpoints, and `2*N` counts minimum path components.

The endpoint traversal and direct signed-state graph are independent checks.
The boundary-word method uses the classical connectivity result to interpret
its counts, as described below. The six-vertex claw components are included
in the first two methods; the third method classifies minimum paths.

## Finite results

| N | Minimum size | Minimum components | Paths | Claws |
|---:|---:|---:|---:|---:|
| 4 | 2 | 2 | 2 | 0 |
| 5 | 3 | 10 | 10 | 0 |
| 6 | 4 | 16 | 12 | 4 |
| 7 | 5 | 14 | 14 | 0 |
| 8 | 6 | 16 | 16 | 0 |
| 9 | 7 | 18 | 18 | 0 |
| 10 | 8 | 20 | 20 | 0 |
| 11 | 9 | 22 | 22 | 0 |
| 12 | 10 | 24 | 24 | 0 |

The general classification and exact `2*N` count are proved in the
associated article, *Minimum components of signed flip graphs: classification
and enumeration*. The computations here are finite checks of that result.
They are not a substitute for the general proof.
The classification up to boundary symmetries and colour permutations in the
JSON is diagnostic and does not change the labelled counts.

The established four-colour connectivity result is used to interpret the
second enumeration as components. The first enumeration does not use that
result to construct its graph. The scripts contain precise assertions;
they are not formal proof-assistant verification of a general theorem.

## Reproduce the new figures

Optional plotting requires matplotlib. Run:

```sh
python3 plot_fan_checks.py --out-dir figures
```

This writes PDF, EPS and PNG versions of a verified fan sweep and the local
forbidden turn. The latter is drawn directly from the recorded certificate.
Generated figures are excluded from this code-and-results repository.

## Integrity

`SHA256SUMS.txt` records the distributed source and result files. It excludes
itself. Re-running the timed enumerations changes timing fields and therefore
its checksums, even when all mathematical counts agree.
