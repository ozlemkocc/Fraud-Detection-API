import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

ARTIFACT_PATH = Path(os.getenv("ARTIFACT_PATH", "fraud_pipeline.joblib"))
artifacts: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    artifacts.update(joblib.load(ARTIFACT_PATH))
    yield
    artifacts.clear()


app = FastAPI(title="Credit Card Fraud Detection API", version="1.1.0", lifespan=lifespan)


class Transaction(BaseModel):
    features: list[float] = Field(..., description="V1..V28, Amount sırasıyla (29 değer)")


class Prediction(BaseModel):
    is_fraud: bool
    fraud_probability: float
    threshold: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(tx: Transaction) -> Prediction:
    columns: list[str] = artifacts["features"]
    if len(tx.features) != len(columns):
        raise HTTPException(422, f"{len(columns)} feature bekleniyor, {len(tx.features)} geldi")

    threshold = float(os.getenv("FRAUD_THRESHOLD", artifacts["threshold"]))
    df = pd.DataFrame([tx.features], columns=columns)
    prob = float(artifacts["pipeline"].predict_proba(df)[0, 1])
    return Prediction(is_fraud=prob >= threshold, fraud_probability=round(prob, 4), threshold=threshold)
