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

ENV PATH="/workspace/.venv/bin:${PATH}" \
    EPHEMERIS_PATH="/opt/ephemeris" \
    PYTHONUNBUFFERED="1"

WORKDIR /workspace/apps/vastrochart-compute
USER appuser

EXPOSE 8080
CMD ["uvicorn", "vastrochart_compute.main:app", "--host", "0.0.0.0", "--port", "8080"]
