from fastapi import APIRouter
from pydantic import BaseModel
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
from joblib import load
import os

router = APIRouter()

# 載入模型與 scaler
model = load(os.path.join("models", "kmeans_model.joblib"))
scaler = load(os.path.join("models", "scaler.joblib"))

# Persona 與建議字典
persona_map = {
    0: {
        "name": "Ｇ型味覺投資家",
        "suggestion": "「別人投資股票，我投資好吃的每一口。」"
    },
    1: {
        "name": "J型快樂即正義",
        "suggestion": "「今天不爽，明天哪來力氣理財？」"
    },
    2: {
        "name": "Ｌ型理性生活工程師",
        "suggestion": "「每一筆支出，都是邏輯優化後的決策。」"
    }
}

# 輸入資料格式
class SpendingInput(BaseModel):
    Food: float
    Transport: float
    Entertainment: float
    Grocery: float
    Others: float

@router.post("/predict/")
def predict(data: SpendingInput):
    # 組成 DataFrame 並計算比例
    df = pd.DataFrame([data.dict()])
    total = df.sum(axis=1)
    for col in df.columns:
        df[col + 'Ratio'] = df[col] / total * 100

    ratio_data = df[[c + 'Ratio' for c in ['Food', 'Transport', 'Entertainment', 'Grocery', 'Others']]]

    # 標準化
    scaled = scaler.transform(ratio_data)

    # 分群預測
    cluster = int(model.predict(scaled)[0])
    persona_info = persona_map.get(cluster, {"name": "未知", "suggestion": "暫無建議"})

    return {
        "cluster": cluster,
        "persona": persona_info["name"],
        "suggestion": persona_info["suggestion"]
    }
