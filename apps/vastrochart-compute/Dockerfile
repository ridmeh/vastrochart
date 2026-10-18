# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm AS builder

# pyswisseph has no prebuilt wheel for every platform (e.g. linux/arm64) and
# builds its C extension from source — needs a compiler in the build stage only.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /workspace
COPY pyproject.toml uv.lock* ./
COPY apps/vastrochart-compute/pyproject.toml apps/vastrochart-compute/pyproject.toml
COPY apps/vastrochart-compute/src apps/vastrochart-compute/src

RUN uv sync --package vastrochart-compute --no-dev --locked

FROM python:3.12-slim-bookworm

RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /workspace
COPY --from=builder /workspace /workspace

# Baked in for production (no host bind-mount available on ACA, unlike
# docker-compose.yml's dev-only mount of this same directory - which still
# works locally, just shadowing these at the same path). Licensing settled
# per ADR-024 (apps/vastrochart-compute/ephemeris/NOTE.md) - safe to ship.
COPY apps/vastrochart-compute/ephemeris/*.se1 /opt/ephemeris/

ENV PATH="/workspace/.venv/bin:${PATH}" \
    EPHEMERIS_PATH="/opt/ephemeris" \
    PYTHONUNBUFFERED="1"

WORKDIR /workspace/apps/vastrochart-compute
USER appuser

EXPOSE 8080
CMD ["uvicorn", "vastrochart_compute.main:app", "--host", "0.0.0.0", "--port", "8080"]
