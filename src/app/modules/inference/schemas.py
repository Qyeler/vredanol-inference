from pydantic import BaseModel


class ClassPrediction(BaseModel):
    label: str
    prob: float


class ClassifyImageInput(BaseModel):
    image: str
    top_k: int = 20
