from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.profile import UserProfile
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.utils.prompts import AVAILABLE_ROLES

router = APIRouter(prefix="/api/roles", tags=["角色"])


def _bigram_similarity(a: str, b: str) -> float:
    """字符级 bigram Jaccard 相似度"""
    def bigrams(s):
        s = s.lower()
        return set(s[i:i+2] for i in range(len(s) - 1)) if len(s) > 1 else {s}
    ba, bb = bigrams(a), bigrams(b)
    if not ba and not bb:
        return 1.0
    intersection = len(ba & bb)
    union = len(ba | bb)
    return intersection / union if union else 0.0


@router.get("/suggestions")
async def get_role_suggestions(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据输入返回相似角色推荐（预设 + 历史自定义）"""
    # 预设角色（排除 custom）
    candidates = [
        {"id": r["id"], "name": r["name"], "icon": r["icon"], "is_preset": True}
        for r in AVAILABLE_ROLES if r["id"] != "custom"
    ]

    # 历史自定义角色（去重）
    custom_names = (
        db.query(UserProfile.custom_role_name)
        .filter(UserProfile.custom_role_name.isnot(None))
        .distinct()
        .all()
    )
    seen_names = {c["name"] for c in candidates}
    for (name,) in custom_names:
        if name and name not in seen_names:
            candidates.append({"id": "custom", "name": name, "icon": "✏️", "is_preset": False})
            seen_names.add(name)

    # 相似度排序
    scored = sorted(
        candidates,
        key=lambda c: _bigram_similarity(q, c["name"]),
        reverse=True,
    )
    return scored[:3]
