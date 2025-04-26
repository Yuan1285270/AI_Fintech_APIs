# 📄 chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# 讀取 .env 檔
load_dotenv()

router = APIRouter()

# 取得 Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={GEMINI_API_KEY}"

# 資料結構
class Message(BaseModel):
    role: str
    message: str

class ChatRequest(BaseModel):
    messages: list[Message]
    persona: str | None = None
    expenses: dict | None = None
    saving_goal: float | None = None
    months: int | None = None

# 自動組 Prompt
def build_intro_prompt(persona: str, expenses: dict, saving_goal: float, months: int):
    return {
        "role": "user",
        "parts": [{
            "text": (
                f"以下是使用者的基本資料，請根據此直接提供個人化儲蓄建議：\\n"
                f"- 消費人格：{persona}\\n"
                f"- 每月平均支出分類：\\n"
                f"  - 食物：{expenses.get('food', 0)} 元\\n"
                f"  - 交通：{expenses.get('transport', 0)} 元\\n"
                f"  - 娛樂：{expenses.get('entertainment', 0)} 元\\n"
                f"  - 生活用品：{expenses.get('grocery', 0)} 元\\n"
                f"  - 其他：{expenses.get('others', 0)} 元\\n"
                f"- 儲蓄目標金額：{saving_goal} 元\\n"
                f"- 預計完成時間：{months} 個月\\n\\n"
                "請直接回覆具體可行的儲蓄建議，包括：可節省金額、可執行的方法、具體步驟。"
            )
        }]
    }

# 核心 API
@router.post("/chatt")
async def chat(chat: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="❌ 缺少 Gemini API 金鑰")

    if not chat.messages or len(chat.messages) == 0:
        raise HTTPException(status_code=400, detail="❌ 請提供至少一筆聊天訊息")

    # 判斷：是要「自動分析模式」還是「一般聊天模式」
    if chat.persona and chat.expenses and chat.saving_goal is not None and chat.months is not None:
        formatted = [build_intro_prompt(chat.persona, chat.expenses, chat.saving_goal, chat.months)] + [
            {
                "role": msg.role,
                "parts": [{"text": msg.message}]
            } for msg in chat.messages
        ]
    else:
        formatted = [
            {
                "role": msg.role,
                "parts": [{"text": msg.message}]
            } for msg in chat.messages
        ]

    try:
        response = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json={"contents": formatted},
            timeout=20  # ⏱️ 加長timeout以防超時
        )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"❌ Gemini API 回應錯誤（{response.status_code}）")

        result = response.json()
        print("📦 Gemini 回傳內容：", result)

        if "candidates" not in result:
            raise HTTPException(status_code=502, detail="❌ Gemini 回傳格式異常，請確認 API Key 或傳送內容。")

        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        return {"reply": reply}

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="❌ 請求 Gemini API 超時，請稍後再試")
    except requests.exceptions.RequestException as e:
        print("🚨 Gemini連線錯誤：", e)
        raise HTTPException(status_code=502, detail="❌ 無法連線到 Gemini API")
    except Exception as e:
        print("🚨 其他錯誤：", e)
        raise HTTPException(status_code=500, detail="❌ 系統內部錯誤")
