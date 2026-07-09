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

See [docs/service-flow.md](docs/service-flow.md) for the UML-style service flow diagram.

See [docs/ml-defense-questions.md](docs/ml-defense-questions.md) for ML theory, project-specific defense questions, expected answers, and practical checks.

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

## Training Datasets

Use datasets according to the model scenario you want to train or fine-tune.

### Food Classification

- [Food-101](https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/) - a strong baseline dataset for food image classification. It contains 101 food categories and 101,000 images. Use it for training or benchmarking a general food classifier.
- [Open Food Facts](https://world.openfoodfacts.org/) - an open food products database with product metadata, barcodes, labels, nutrition facts, and user-contributed product images. It is useful for product-oriented food recognition and barcode-to-product enrichment.
- [Open Food Facts Images on AWS Open Data](https://registry.opendata.aws/openfoodfacts-images/) - image dataset for Open Food Facts products. Use it when training models on real product packaging and labels.

### Grocery And Product Recognition

- [Grocery Store Dataset](https://github.com/marcusklasson/GroceryStoreDataset) - natural images of grocery items taken in stores. Useful for grocery classification and fine-grained product/category recognition.
- [Object Detection Grocery Products](https://github.com/tobiagru/ObjectDetectionGroceryProducts) - grocery product detection dataset with shelf/product images. Useful when the model needs to detect products inside a larger scene.
- [Amazon Berkeley Objects](https://amazon-berkeley-objects.s3.amazonaws.com/index.html) - large product-image dataset with product metadata and multiple images per item. Useful for general product recognition experiments.

### Shelf Detection And Retail Scenes

- [SKU-110K](https://github.com/eg4000/sku110k_cvpr19) - retail shelf dataset for dense product detection. Use it if the target task is not just classification, but finding product regions on crowded shelves.

### Barcode-Related Data

- [Open Food Facts Product Database](https://huggingface.co/datasets/openfoodfacts/product-database) - product metadata with barcodes. Useful for matching scanned barcodes to product names, brands, ingredients, and nutrition data.
- [OCR Barcodes Detection](https://huggingface.co/datasets/UniqueData/ocr-barcodes-detection) - barcode detection/OCR dataset with grocery goods and annotated barcode regions. Useful if the service needs to detect barcode areas from images before decoding them.

### Recommended Training Strategy

1. Start with Food-101 for food category classification.
2. Fine-tune on grocery/product photos closer to the target frontend use case.
3. Use Open Food Facts for barcode mapping and product metadata.
4. Use SKU-110K or grocery detection datasets if the model must detect products inside shelves or complex scenes.
5. Keep a private validation set from real user-like photos to measure product quality, not only benchmark accuracy.

Always check dataset licenses and attribution requirements before using a dataset in production.

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
