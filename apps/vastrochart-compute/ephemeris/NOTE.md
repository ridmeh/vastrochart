# Swiss Ephemeris Data Files

This directory holds the Swiss Ephemeris binary data files (`.se1`) that give
`pyswisseph` full precision. They are **not** committed to git (large
binaries, license-sensitive redistribution — see `.gitignore`), so every
dev/deploy environment fetches them independently.

## Licensing: resolved

ADR-001's open AGPL question is settled by ADR-024 (public, open-core repo
from Day 2) — comply via publishing source, no commercial license needed.
No longer a blocker to fetching these files.

## Current files (fetched 2026-10-12)

From the official Swiss Ephemeris GitHub repo
(`github.com/aloistr/swisseph`, folder `ephe`), build dated 2026-05-26:

- `sepl_18.se1` — planets (Sun–Pluto), covering roughly 1800–2399 CE
- `semo_18.se1` — Moon, same range
- `seas_18.se1` — main asteroids, same range

These three cover VAstroChart's near-term golden-data and dev needs. Wider
date coverage (the roadmap's "DE431 compressed subset, ~13,000 BCE–17,000 CE")
is a separate, larger fetch — not yet pinned; add more `se*_NN.se1` files
from the same source as date range needs grow.

To re-fetch:
```bash
cd apps/vastrochart-compute/ephemeris
for f in sepl_18.se1 semo_18.se1 seas_18.se1; do
  curl -sS -L -o "$f" "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/$f"
done
```

## Wiring

`vastrochart_compute.compute.ephemeris_init.configure_ephemeris_path()` calls
`swe.set_ephe_path()` before any ephemeris computation, pointed at
`$EPHEMERIS_PATH` (default: this directory). Without it, pyswisseph silently
uses the lower-precision Moshier fallback — this bit us once already (see
`docs/known-reference-tool-deltas.md`), so don't skip calling it.

`docker-compose.yml` mounts this directory read-only into the container at
`/opt/ephemeris`. `/readyz` reports `"fallback": "moshier"` when no `.se1`
files are present at `$EPHEMERIS_PATH`.
