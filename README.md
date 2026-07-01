# Vredanol Inference

Backend ML-worker for the Vredanol service. The worker receives an image from the main backend, runs ONNX classification, and returns the most likely product or food categories.

The frontend and main product backend are assumed to be separate parts of the system. This repository focuses on the inference layer: image preprocessing, model loading, background task execution, and classification response formatting.

## Features

- Image classification for food and grocery/product scenarios.
- ONNX Runtime inference with ConvNeXt Tiny models.
- Async task execution through Celery.
- Redis broker/result backend support.
- Base64 image input, including browser data URLs.
- Configurable `top_k` predictions.
- Model and class-file paths configured through `.env`.
- Docker and Docker Compose deployment.
- Structured logging with `structlog`.

## Product Context

In the full Vredanol product, inference can be used together with:

- user authorization;
- user profile and history;
- barcode recognition;
- editable product cards;
- analytics for recognition quality and user activity.

See [SERVICE_PRESENTATION.md](SERVICE_PRESENTATION.md) for a presentation-style product and technical overview.

## Model Files

Runtime model artifacts are expected in `models/` and are intentionally not committed to Git because model weights are large.

For the current food model, download these files from the Hugging Face bucket `Fabul0n/vredanol-inference`:

- `convnext_tiny_food.data`
- `convnext_tiny_food.onnx.data`
- `food_classes.txt`

Expected local structure:

```text
models/
  convnext_tiny_food.data
  convnext_tiny_food.onnx.data
  food_classes.txt
```

## Environment

Create `src/.env` from `src/.env.example` and set the model paths:

```env
MODEL_PATH=./models/convnext_tiny_food.data
MODEL_CLASSES_PATH=./models/food_classes.txt
MODEL_PROVIDERS=["CPUExecutionProvider"]
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_INFERENCE_QUEUE=inference
```

The local `src/.env` file is ignored by Git.

## Quick Start

Install dependencies:

```bash
uv sync
```

Run the inference worker:

```bash
uv run celery -A src.app.core.celery.settings worker -Q inference -l INFO
```

The worker registers the Celery task:

```text
inference.classify
```

## Docker Compose

The project includes a worker service in `docker-compose.yml`.

```bash
docker compose up --build -d
```

The compose service expects:

- `src/.env` with runtime configuration;
- model files in `models/`;
- external Docker network `vredanol_net`;
- Redis available through the configured broker URL.

## Task Payload

Input:

```json
{
  "image": "<base64-image>",
  "top_k": 20
}
```

Output:

```json
[
  {
    "label": "banana",
    "prob": 0.91
  },
  {
    "label": "bread",
    "prob": 0.04
  }
]
```

## How Inference Works

1. The worker receives a Celery task.
2. The model is loaded if it is not ready yet.
3. The image is decoded from base64.
4. The image is converted to RGB.
5. The shorter side is resized to `MODEL_RESIZE_SIZE`.
6. The image is center-cropped to `MODEL_IMAGE_SIZE`.
7. Pixel values are normalized with configured mean/std.
8. ONNX Runtime runs the model.
9. Logits are converted to probabilities.
10. The worker returns top predictions with labels and probabilities.

## Project Structure

```text
src/app/core/
  config.py          # environment settings
  logger.py          # structured logging
  celery/            # Celery app setup

src/app/modules/inference/
  schemas.py         # task and prediction schemas
  service.py         # image preprocessing and ONNX inference
  tasks.py           # Celery task entrypoint

models/
  .gitkeep           # model artifacts are stored locally
```

## Notes

- Model files are not committed to Git.
- `src/.env` is not committed to Git.
- The current local food model has 20 classes.
- The default model input size is `224x224`.
- The default ONNX provider is CPU.
