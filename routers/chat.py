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
            "- 味覺投資家：近一半支出花在飲食上，講究品質與療癒感，不論外食還是自煮都追求儀式感。娛樂開支極低，偏好安靜獨處，重視細節與生活品質。\n"
            "- 快樂即正義：娛樂支出佔比極高，可能達六成以上。喜歡即時快樂，愛玩遊戲、追劇、參加社交活動，是感受派、體驗派的代表。\n"
            "- 理性生活工程師：支出分布平均且穩定，有紀律、有邏輯，偏好平衡與規劃。注重長期目標，適合分段實踐儲蓄計劃。\n\n"
            "2. 每月各項消費平均金額\n\n"
            "請先詢問使用者以下資訊：\n"
            "- 儲蓄目標金額\n"
            "- 預計完成儲蓄的時間（月數）\n"
            "- 每月固定收入\n\n"
            "在使用者提供上述資訊後，請根據其消費人格類型與儲蓄目標，給出明確、有邏輯、具體且可量化的儲蓄建議。\n"
            "每一項建議請包含：\n"
            "- 預估可節省金額\n"
            "- 可實行的方法與行動策略（例如：固定比例、特定行為的替代方案、結構性變動等）\n\n"
            "如果使用者偏離主題，請適當引導回到儲蓄與消費規劃的主軸。"
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
