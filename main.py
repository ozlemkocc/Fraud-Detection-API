from fastapi import FastAPI
import joblib
import pandas as pd
from pydantic import BaseModel

app = FastAPI()

# Senin dosyalarının tam isimleri
model = joblib.load('fraud_model.joblib')
scaler = joblib.load('scaler.joblib')

class Transaction(BaseModel):
    features: list

@app.post("/predict")
def predict(transaction: Transaction):
    df = pd.DataFrame([transaction.features], columns=model.feature_names_in_)
    # Amount sütununu ölçeklendir
    df.iloc[:, -1] = scaler.transform(df.iloc[:, [-1]])
    
    prob = model.predict_proba(df)[0][1]
    prediction = int(model.predict(df)[0])
    
    return {
        "is_fraud": prediction, 
        "probability": f"%{prob*100:.2f}",
        "action": "BLOKE ET" if prediction == 1 else "ONAYLA"
    }
