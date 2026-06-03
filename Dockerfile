# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable --no-install-project

COPY README.md ./
COPY src/app ./src/app
COPY models ./models

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable

FROM python:3.12-slim
ENV UID=2000
ENV GID=2000
ENV FILE_LOG_DIR=/home/python/logs/celery
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:${PATH}"

RUN groupadd -g "${GID}" python \
    && useradd --create-home --no-log-init --shell /bin/bash -u "${UID}" -g "${GID}" python \
    && mkdir -p /home/python/logs \
    && chown -R "${UID}:${GID}" /home/python/logs

WORKDIR /home/python

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=python:python /app/src ./src
COPY --from=builder --chown=python:python /app/models ./models

USER python

CMD ["sh", "-c", "celery -A src.app.core.celery.settings worker -Q ${CELERY_INFERENCE_QUEUE:-inference} -l INFO"]
