import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    APP_NAME: str = "Vredanol inference"
    APP_DESCRIPTION: str | None = None
    APP_VERSION: str | None = None
    LICENSE_NAME: str | None = None
    CONTACT_NAME: str | None = None
    CONTACT_EMAIL: str | None = None


class ModelSettings(BaseSettings):
    MODEL_PATH: str = "./models/model.onnx"
    MODEL_LABELS: list[str] = []
    MODEL_CLASSES_PATH: str = "./models/classes.txt"
    MODEL_IMAGE_SIZE: int = 224
    MODEL_RESIZE_SIZE: int = 256
    MODEL_NORMALIZE_MEAN: list[float] = [0.485, 0.456, 0.406]
    MODEL_NORMALIZE_STD: list[float] = [0.229, 0.224, 0.225]
    MODEL_INPUT_NAME: str | None = None
    MODEL_OUTPUT_NAME: str | None = None
    MODEL_PROVIDERS: list[str] = ["CPUExecutionProvider"]
    MODEL_STARTUP_STRICT: bool = True


class CelerySettings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str | None = "redis://localhost:6379/2"
    CELERY_TIMEZONE: str = "UTC"
    CELERY_INFERENCE_QUEUE: str = "inference"


class FileLoggerSettings(BaseSettings):
    FILE_LOG_DIR: str | None = None
    FILE_LOG_MAX_BYTES: int = 10 * 1024 * 1024
    FILE_LOG_BACKUP_COUNT: int = 5
    FILE_LOG_FORMAT_JSON: bool = True
    FILE_LOG_LEVEL: str = "INFO"
    FILE_LOG_INCLUDE_REQUEST_ID: bool = True
    FILE_LOG_INCLUDE_PATH: bool = True
    FILE_LOG_INCLUDE_METHOD: bool = True
    FILE_LOG_INCLUDE_CLIENT_HOST: bool = True
    FILE_LOG_INCLUDE_STATUS_CODE: bool = True


class ConsoleLoggerSettings(BaseSettings):
    CONSOLE_LOG_LEVEL: str = "INFO"
    CONSOLE_LOG_FORMAT_JSON: bool = False
    CONSOLE_LOG_INCLUDE_REQUEST_ID: bool = True
    CONSOLE_LOG_INCLUDE_PATH: bool = True
    CONSOLE_LOG_INCLUDE_METHOD: bool = True
    CONSOLE_LOG_INCLUDE_CLIENT_HOST: bool = True
    CONSOLE_LOG_INCLUDE_STATUS_CODE: bool = True


class Settings(
    AppSettings,
    ModelSettings,
    CelerySettings,
    FileLoggerSettings,
    ConsoleLoggerSettings,
):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
