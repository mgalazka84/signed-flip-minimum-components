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
```

Both scripts stop with an assertion error on a failed check. Do not run them
with `python -O`, which disables assertions. Counts are deterministic; the
`seconds` field in the signed-state results depends on the machine.

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

The observed count `2*N` for N>=7 is checked only in this finite range.
These computations do not prove that count for arbitrary N.
The classification up to boundary symmetries and colour permutations in the
JSON is diagnostic and does not change the labelled counts.

The established four-colour connectivity result is used to interpret the
second enumeration as components. The first enumeration does not use that
result to construct its graph. The scripts contain precise assertions;
they are not formal proof-assistant verification of a general theorem.

## Integrity

`SHA256SUMS.txt` records the distributed source and result files. It excludes
itself. Re-running the signed enumeration changes timing fields and therefore
its checksums, even when all mathematical counts agree.
