import uuid
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.models.shared_scenario import SharedScenario
from backend.models.user_scenario import UserScenario
from backend.schemas import ScenarioGenerate, ScenarioResponse, MessageResponse
from backend.api.deps import get_current_user
from backend.services.llm_service import LLMService

router = APIRouter(prefix="/api/scenarios", tags=["场景"])

DEDUP_DAYS = 7  # 用户 N 天内见过的场景不重复出现


def _user_scenario_to_response(us: UserScenario) -> dict:
    ss = us.shared_scenario
    return {
        "id": us.id,
        "user_id": us.user_id,
        "session_id": us.session_id,
        "title": ss.title,
        "description": ss.description,
        "context": ss.context,
        "role": ss.role,
        "language": ss.language,
        "is_selected": us.is_selected,
        "is_practiced": us.is_practiced,
        "created_at": us.created_at,
    }


@router.post("/generate", response_model=List[ScenarioResponse])
async def generate_scenarios(
    generate_data: ScenarioGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成 N 个口语场景（共享池复用 + 用户去重）"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先设置个人配置（角色和 target_language）")

    # 清除旧关联
    db.query(UserScenario).filter(UserScenario.user_id == current_user.id).delete()
    db.commit()

    # 查找用户最近 DEDUP_DAYS 天看过的场景 ID
    cutoff = datetime.utcnow() - timedelta(days=DEDUP_DAYS)
    recent_ids = {
        row.shared_scenario_id
        for row in db.query(UserScenario.shared_scenario_id).filter(
            UserScenario.user_id == current_user.id,
            UserScenario.created_at >= cutoff,
        ).all()
    }

    # 从共享池取该用户未见过的场景
    shared = db.query(SharedScenario).filter(
        SharedScenario.role == profile.role,
        SharedScenario.language == profile.target_language,
        SharedScenario.proficiency_level == profile.proficiency_level,
        ~SharedScenario.id.in_(recent_ids) if recent_ids else True,
    ).limit(generate_data.count).all()

    # 不够则调 LLM 补充
    if len(shared) < generate_data.count:
        llm_service = LLMService()
        scenarios_data = await asyncio.to_thread(
            llm_service.generate_scenarios,
            role=profile.role,
            custom_role_name=profile.custom_role_name,
            language=profile.target_language,
            count=generate_data.count,
            proficiency_level=profile.proficiency_level,
        )
        if not isinstance(scenarios_data, list):
            scenarios_data = [scenarios_data]

        existing_titles = {s.title for s in shared}
        for sd in scenarios_data:
            title = sd.get("title", "未命名场景")
            if title in existing_titles:
                continue
            from sqlalchemy.exc import IntegrityError
            ss = SharedScenario(
                role=profile.role,
                language=profile.target_language,
                proficiency_level=profile.proficiency_level,
                title=title,
                description=sd.get("description", ""),
                context=sd.get("context", ""),
            )
            try:
                db.add(ss)
                db.flush()
                shared.append(ss)
                existing_titles.add(title)
            except IntegrityError:
                db.rollback()
                # 标题重复，从共享池捞已有的
                existing = db.query(SharedScenario).filter_by(
                    role=profile.role, language=profile.target_language,
                    proficiency_level=profile.proficiency_level, title=title,
                ).first()
                if existing and existing.id not in {s.id for s in shared}:
                    shared.append(existing)
                    existing_titles.add(title)
            if len(shared) >= generate_data.count:
                break
        db.commit()
        for s in shared:
            db.refresh(s)

    # 关联到当前用户
    session_id = str(uuid.uuid4())
    user_scenarios = []
    for ss in shared[:generate_data.count]:
        us = UserScenario(
            user_id=current_user.id,
            shared_scenario_id=ss.id,
            session_id=session_id,
            is_selected=False,
        )
        db.add(us)
        user_scenarios.append(us)
    db.commit()
    for us in user_scenarios:
        db.refresh(us)

    return [_user_scenario_to_response(us) for us in user_scenarios]


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的场景列表"""
    user_scenarios = db.query(UserScenario).filter(
        UserScenario.user_id == current_user.id
    ).order_by(UserScenario.created_at.desc()).limit(20).all()
    return [_user_scenario_to_response(us) for us in user_scenarios]


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景详情（scenario_id 为 UserScenario.id）"""
    us = db.query(UserScenario).filter(
        UserScenario.id == scenario_id,
        UserScenario.user_id == current_user.id,
    ).first()
    if not us:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")
    return _user_scenario_to_response(us)


@router.post("/{scenario_id}/select", response_model=MessageResponse)
async def select_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """选择场景"""
    db.query(UserScenario).filter(
        UserScenario.user_id == current_user.id,
        UserScenario.is_selected == True
    ).update({"is_selected": False})

    us = db.query(UserScenario).filter(
        UserScenario.id == scenario_id,
        UserScenario.user_id == current_user.id,
    ).first()
    if not us:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")

    us.is_selected = True
    db.commit()
    return MessageResponse(message="场景选择成功")


@router.post("/{scenario_id}/practiced", response_model=MessageResponse)
async def mark_scenario_practiced(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记场景已练习"""
    us = db.query(UserScenario).filter(
        UserScenario.id == scenario_id,
        UserScenario.user_id == current_user.id,
    ).first()
    if not us:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")
    us.is_practiced = True
    db.commit()
    return MessageResponse(message="已标记为已练习")


@router.delete("/{scenario_id}", response_model=MessageResponse)
async def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户场景关联"""
    us = db.query(UserScenario).filter(
        UserScenario.id == scenario_id,
        UserScenario.user_id == current_user.id,
    ).first()
    if not us:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")

    db.delete(us)
    db.commit()
    return MessageResponse(message="场景删除成功")
