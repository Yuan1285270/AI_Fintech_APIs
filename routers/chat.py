from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# 載入本地 .env（開發用）
load_dotenv()

router = APIRouter()

# 從環境變數中取得 Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={GEMINI_API_KEY}"

# 使用者訊息格式
class Message(BaseModel):
    role: str
    message: str

# 請求格式
class ChatRequest(BaseModel):
    messages: list[Message]

# 角色提示（只會在第一輪加入）
INTRO_PROMPT = {
    "role": "user",
    "parts": [{
        "text": (
            "你是一位理財儲蓄助理，專門根據使用者的消費個性與儲蓄目標，提供個人化、具體可執行計畫。\n"
            "使用者會提供以下兩項資訊：\n\n"
            "1. 消費人格（請從以下三種中選擇其一）：\n"
            "- 美食至上型：將近一半支出花在飲食上，對吃非常講究，不論是外食還是料理都有儀式感。娛樂支出極低，個性偏內向，重視生活品質與細節。\n"
            "- 重娛樂享樂型：娛樂支出佔比非常高，可能高達六成以上。重視即時快樂與放鬆，喜歡遊戲、影音、社交活動等。\n"
            "- 穩健節奏型：花費分布平均，沒有明顯偏重項目。生活有規律，個性務實、有紀律，適合循序漸進地達成儲蓄目標。\n\n"
            "2. 每月各項消費平均金額\n\n"
            "請先詢問使用者儲蓄目標金額與時間以及每月收入，在使用者提供後，再根據他的人格類型與儲蓄計劃，給予明確、有邏輯，具體且可量化的儲蓄計劃，每一項建議請包含預估可節省金額與實行方式\n"
            "如果偏離主題請拉回。"
        )
    }]
}

@router.post("/chat")
async def chat(chat: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="❌ 缺少 Gemini API 金鑰")

    if not chat.messages or len(chat.messages) == 0:
        raise HTTPException(status_code=400, detail="❌ 請提供至少一筆聊天訊息")

    # 判斷是否已經有角色引導提示（避免重複加）
    first_message = chat.messages[0].message.lower()
    has_intro = "理財儲蓄助理" in first_message and "消費人格" in first_message

    # 組成 Gemini 專用格式
    formatted = (
        [] if has_intro else [INTRO_PROMPT]
    ) + [
        {
            "role": msg.role,
            "parts": [{ "text": msg.message }]
        } for msg in chat.messages
    ]

    try:
        response = requests.post(
            GEMINI_URL,
            headers={ "Content-Type": "application/json" },
            json={ "contents": formatted }
        )

        result = response.json()
        print("📦 Gemini 回傳內容：", result)

        if "candidates" not in result:
            return {
                "error": result.get("error", {}),
                "message": "Gemini 回傳錯誤格式，請確認 API key 或傳送內容。"
            }

        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        return { "reply": reply }

    except Exception as e:
        print("🚨 Gemini 回應錯誤：", e)
        raise HTTPException(status_code=500, detail="Gemini API 錯誤")
