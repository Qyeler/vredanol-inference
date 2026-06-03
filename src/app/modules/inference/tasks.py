"""Celery tasks for ONNX inference."""

import asyncio

import structlog

from src.app.core.celery.app import celery_app
from src.app.modules.inference.schemas import ClassifyImageInput
from src.app.modules.inference.service import inference_service

logger = structlog.get_logger(__name__)


@celery_app.task(name="inference.classify")
def classify_task(payload: dict) -> list[dict]:
    if not inference_service.is_ready():
        asyncio.run(inference_service.startup())

    request = ClassifyImageInput.model_validate(payload)
    image_bytes = inference_service.decode_base64_image(request.image)

    result = inference_service.classify_image(image_bytes=image_bytes, top_k=request.top_k)
    logger.info("inference.classify.completed", top_k=request.top_k, predictions_count=len(result))
    return [item.model_dump() for item in result]
