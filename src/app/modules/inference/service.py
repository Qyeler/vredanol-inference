import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import onnxruntime as ort
import structlog
from PIL import Image

from ...core.config import settings
from .schemas import ClassPrediction

LOGGER = structlog.get_logger(__name__)


class InferenceService:
    def __init__(self) -> None:
        self._session: ort.InferenceSession | None = None
        self._input_name: str | None = None
        self._output_name: str | None = None
        self._labels: list[str] = []

    async def startup(self) -> None:
        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            message = "Model file not found on startup"
            LOGGER.warning(message, model_path=str(model_path))
            if settings.MODEL_STARTUP_STRICT:
                raise RuntimeError(f"{message}: {model_path}") from None
            return

        try:
            self._session = ort.InferenceSession(str(model_path), providers=settings.MODEL_PROVIDERS)
            self._input_name = settings.MODEL_INPUT_NAME or self._session.get_inputs()[0].name
            self._output_name = settings.MODEL_OUTPUT_NAME or self._session.get_outputs()[0].name
            self._labels = self._load_labels()
            LOGGER.info(
                "ONNX model loaded",
                model_path=str(model_path),
                input_name=self._input_name,
                output_name=self._output_name,
                labels_count=len(self._labels),
            )
        except Exception as exc:
            LOGGER.exception("Failed to load ONNX model", error=str(exc), model_path=str(model_path))
            self._session = None
            self._input_name = None
            self._output_name = None
            self._labels = []
            if settings.MODEL_STARTUP_STRICT:
                raise

    async def shutdown(self) -> None:
        self._session = None
        self._input_name = None
        self._output_name = None
        self._labels = []

    def is_ready(self) -> bool:
        return self._session is not None and self._input_name is not None and self._output_name is not None

    def classify_image(self, image_bytes: bytes, top_k: int = 20) -> list[ClassPrediction]:
        if not self.is_ready():
            raise RuntimeError("Model is not loaded. Check MODEL_PATH and startup logs.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        assert self._session is not None
        assert self._input_name is not None
        assert self._output_name is not None

        try:
            input_batch = self._preprocess_image(image_bytes)
            raw_output = self._session.run([self._output_name], {self._input_name: input_batch})[0]
            logits = np.asarray(raw_output).squeeze()
            if logits.ndim == 0:
                logits = np.asarray([float(logits)])

            probabilities = self._softmax(logits)
            top_k = min(top_k, probabilities.shape[0])
            top_indices = np.argsort(probabilities)[::-1][:top_k]

            top_scored = [
                ClassPrediction(
                    label=self._label_for(int(idx)),
                    prob=float(probabilities[idx]),
                )
                for idx in top_indices
            ]
            return top_scored
        except Exception as exc:
            LOGGER.exception("Inference failed", error=str(exc))
            raise RuntimeError("Inference failed due to internal error.") from exc

    @staticmethod
    def _softmax(values: np.ndarray) -> np.ndarray:
        shifted = values - np.max(values)
        exp_values = np.exp(shifted)
        denominator = np.sum(exp_values)
        if denominator == 0:
            return np.zeros_like(values, dtype=np.float64)
        return exp_values / denominator

    def _label_for(self, class_id: int) -> str:
        if 0 <= class_id < len(self._labels):
            return self._labels[class_id]
        return str(class_id)

    @staticmethod
    def decode_base64_image(image_base64: str) -> bytes:
        payload = image_base64
        if "," in image_base64 and image_base64.startswith("data:"):
            payload = image_base64.split(",", 1)[1]
        return base64.b64decode(payload)

    @staticmethod
    def _center_crop(pil_image: Image.Image, crop_size: int) -> Image.Image:
        width, height = pil_image.size
        left = max((width - crop_size) // 2, 0)
        top = max((height - crop_size) // 2, 0)
        right = left + crop_size
        bottom = top + crop_size
        return pil_image.crop((left, top, right, bottom))

    @staticmethod
    def _resize_shorter_side(pil_image: Image.Image, shorter_side: int) -> Image.Image:
        width, height = pil_image.size
        if width <= 0 or height <= 0:
            raise ValueError("Invalid image dimensions.")

        if width < height:
            new_width = shorter_side
            new_height = int(round(height * (shorter_side / width)))
        else:
            new_height = shorter_side
            new_width = int(round(width * (shorter_side / height)))

        return pil_image.resize((new_width, new_height), Image.Resampling.BILINEAR)

    def _preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image = self._resize_shorter_side(image, settings.MODEL_RESIZE_SIZE)
        image = self._center_crop(image, settings.MODEL_IMAGE_SIZE)

        image_np = np.asarray(image, dtype=np.float32) / 255.0
        image_np = np.transpose(image_np, (2, 0, 1))

        mean = np.asarray(settings.MODEL_NORMALIZE_MEAN, dtype=np.float32).reshape(3, 1, 1)
        std = np.asarray(settings.MODEL_NORMALIZE_STD, dtype=np.float32).reshape(3, 1, 1)
        image_np = (image_np - mean) / std

        return image_np[np.newaxis, ...].astype(np.float32)

    def _load_labels(self) -> list[str]:
        classes_path = Path(settings.MODEL_CLASSES_PATH)
        if classes_path.exists():
            labels = [line.strip() for line in classes_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if labels:
                return labels
        if settings.MODEL_LABELS:
            return settings.MODEL_LABELS
        return []


inference_service = InferenceService()
