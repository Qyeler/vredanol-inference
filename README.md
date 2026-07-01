# Vredanol inference

## Model files

Runtime model artifacts are expected in `models/` and are intentionally not committed.
For the food model, download these files from `Fabul0n/vredanol-inference` on Hugging Face:

- `convnext_tiny_food.data`
- `convnext_tiny_food.onnx.data`
- `food_classes.txt`

Then configure `src/.env`:

```env
MODEL_PATH=./models/convnext_tiny_food.data
MODEL_CLASSES_PATH=./models/food_classes.txt
```

## `uv sync` - install dependencies
## `uv run celery -A src.app.core.celery.settings worker -Q inference -l INFO` - run inference worker
## Task payload example:
## `{"image":"<base64-image>","top_k":20}`
