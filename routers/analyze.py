from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter()

# 👉 輸入資料模型
class SavingPlanInput(BaseModel):
    start_date: str
    end_date: str
    target_amount: float
    current_saved: float
    daily_amount: float
    today_str: Optional[str] = None
    threshold: Optional[float] = 0.95

# 👉 儲蓄進度分析函式（直接貼上你的函式）
def analyze_saving_progress(
    start_date: str,
    end_date: str,
    target_amount: float,
    current_saved: float,
    daily_amount: float,
    today_str: str = None,
    threshold: float = 0.95
) -> dict:
    today = datetime.strptime(today_str, "%Y-%m-%d").date() if today_str else datetime.now().date()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    if current_saved >= target_amount:
        status = "completed"
        return {
            "status": status,
            "current_saved": current_saved,
            "target_amount": target_amount,
            "progress_ratio": 1.0,
            "today": today,
            "message": f"儲蓄計畫已完成！你總共存了 {current_saved} 元，成功達成目標 🎉！"
        }

    if today > end:
        gap = max(round(target_amount - current_saved, 2), 0)
        status = "outdated"
        return {
            "status": status,
            "current_saved": current_saved,
            "target_amount": target_amount,
            "progress_ratio": round(current_saved / target_amount, 4) if target_amount > 0 else 1.0,
            "today": today,
            "message": f"儲蓄計畫已結束。你總共存了 {current_saved} 元，離目標還剩 {gap} 元。"
        }

    total_days = (end - start).days + 1
    days_passed = (today - start).days + 1
    days_passed = max(0, min(days_passed, total_days))

    expected_saved = min(round(daily_amount * days_passed, 2), target_amount)

    progress_ratio = current_saved / expected_saved if expected_saved > 0 else 1.0
    status = "behind" if progress_ratio < threshold else "on-track"
    gap = round(expected_saved - current_saved, 2) if status == "behind" else 0

    return {
        "start_date": str(start),
        "end_date": str(end),
        "target_amount": target_amount,
        "daily_amount": daily_amount,
        "status": status,
        "current_saved": current_saved,
        "expected_saved": expected_saved,
        "progress_ratio": round(progress_ratio, 4),
        "gap": gap,
        "days_passed": days_passed,
        "total_days": total_days,
        "message": (
            f"📉 你已存 {current_saved} 元，照進度應該存 {expected_saved} 元（進度比 {round(progress_ratio*100,1)}%），落後 {gap} 元。"
            if status == "behind"
            else f"✅ 儲蓄進度良好（{round(progress_ratio*100,1)}%），繼續加油！"
        )
    }

# 👉 FastAPI 路由
@router.post("/analyze")
def analyze(data: SavingPlanInput):
    result = analyze_saving_progress(**data.dict())
    return result
