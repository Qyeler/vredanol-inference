# Vredanol inference

## `uv sync` - install dependencies
## `uv run celery -A src.app.core.celery.settings worker -Q inference -l INFO` - run inference worker
## Task payload example:
## `{"image":"<base64-image>","top_k":20}`
