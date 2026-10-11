# Swiss Ephemeris Data Files

This directory holds the Swiss Ephemeris binary data files (`.se1`) that give
`pyswisseph` full precision across its supported date range. They are
deliberately **not** committed to git (large binaries, see `.gitignore`) and
**not** auto-downloaded by this scaffold.

## Why not auto-fetched

Two open items from `docs/06-roadmap.md` govern how these files are sourced
and distributed, and neither is decided yet:

1. **Swiss Ephemeris AGPL licensing** (ADR-001 in `docs/05-decisions.md`) —
   comply by publishing MCP server source, or buy the commercial license
   (~€400 one-time). This affects how we're allowed to ship/redistribute.
2. **Which specific subset** ("DE431 compressed subset, ~15 MB") — the exact
   file list (date range, which planets) hasn't been pinned yet.

## Until then

Without files here, `pyswisseph` automatically falls back to its built-in
**Moshier** analytical ephemeris — lower precision, but functional for Day 2
scaffolding and local hello-world testing. `/readyz` reports this via
`"fallback": "moshier"`.

## To add the real files later

Download from https://www.astro.com/ftp/swisseph/ephe/ (e.g. `sepl_18.se1`,
`semo_18.se1`, `seas_18.se1` for a multi-century range) and place them in this
directory. `docker-compose.yml` mounts it read-only into the container at
`/opt/ephemeris`.
