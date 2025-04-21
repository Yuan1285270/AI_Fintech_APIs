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

def analyze_saving_progress(
    start_date: str,
    end_date: str,
    target_amount: float,
    current_saved: float,
) -> dict:
    
    threshold = 0.95
    today = datetime.now().date()
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    total_days = (end - start).days + 1
    days_passed = (today - start).days + 1
    days_passed = max(0, min(days_passed, total_days))

    daily_amount = target_amount / total_days if total_days > 0 else target_amount
    expected_saved = min(round(daily_amount * days_passed, 2), target_amount)

    # ✅ 已完成
    if current_saved >= target_amount:
        gap = round(current_saved - target_amount, 2)
        gap_status = "ahead" if gap >= 0 else "behind"
        return {
            "status": "completed",
            "current_saved": current_saved,
            "expected_saved": target_amount,
            "progress_ratio": 100.0,
            "gap_status": gap_status,
            "gap": abs(gap),
            "days_passed": days_passed,
            "total_days": total_days
        }

    # ✅ 已過期
    if today > end:
        gap = round(current_saved - target_amount, 2)
        gap_status = "ahead" if gap >= 0 else "behind"
        return {
            "status": "outdated",
            "current_saved": current_saved,
            "expected_saved": target_amount,
            "progress_ratio": round(min(current_saved / target_amount, 1.0) * 100, 1),
            "gap_status": gap_status,
            "gap": abs(gap),
            "days_passed": days_passed,
            "total_days": total_days
        }

    # ✅ 一般狀態
    raw_ratio = current_saved / expected_saved if expected_saved > 0 else 1.0
    progress_ratio = min(raw_ratio, 1.0)
    status = "behind" if progress_ratio < threshold else "on-track"
    gap = round(current_saved - expected_saved, 2)
    gap_status = "ahead" if gap >= 0 else "behind"

    return {
        "status": status,
        "current_saved": current_saved,
        "expected_saved": expected_saved,
        "progress_ratio": round(progress_ratio * 100, 1),
        "gap_status": gap_status,
        "gap": abs(gap),
        "days_passed": days_passed,
        "total_days": total_days
    }


# 👉 FastAPI 路由
@router.post("/analyze")
def analyze(data: SavingPlanInput):
    result = analyze_saving_progress(**data.dict())
    return result
