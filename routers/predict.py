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
        "name": "🍱 美食至上型",
        "suggestion": "你偏好花在吃的與日常消費，推薦你使用料理推薦與比價工具，幫助你吃得好也吃得省。"
    },
    1: {
        "name": "🕹️ 重娛樂享樂型",
        "suggestion": "你偏好把錢花在娛樂上！建議設定每月娛樂上限，避免超支；也可以訂閱遊戲/影音月卡省更多。"
    },
    2: {
        "name": "🏠 穩健節奏型",
        "suggestion": "你消費分配平衡，代表你是理性規劃型，推薦使用預算工具與長期儲蓄功能來強化理財計畫。"
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
