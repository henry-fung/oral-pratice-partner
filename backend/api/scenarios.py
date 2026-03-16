import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.models.scenario import Scenario
from backend.schemas import ScenarioGenerate, ScenarioResponse, ScenarioSelect, MessageResponse
from backend.api.deps import get_current_user
from backend.services.llm_service import LLMService

router = APIRouter(prefix="/api/scenarios", tags=["场景"])


@router.post("/generate", response_model=List[ScenarioResponse])
async def generate_scenarios(
    generate_data: ScenarioGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成 N 个口语场景"""
    # 获取用户配置
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先设置个人配置（角色和 target_language）"
        )

    # 调用 LLM 生成场景
    llm_service = LLMService()
    scenarios_data = llm_service.generate_scenarios(
        role=profile.role,
        custom_role_name=profile.custom_role_name,
        language=profile.target_language,
        count=generate_data.count,
        proficiency_level=profile.proficiency_level
    )

    # 确保返回的是列表
    if not isinstance(scenarios_data, list):
        scenarios_data = [scenarios_data]

    # 生成 session_id
    session_id = str(uuid.uuid4())

    # 保存到数据库
    created_scenarios = []
    for scenario_data in scenarios_data:
        scenario = Scenario(
            user_id=current_user.id,
            session_id=session_id,
            title=scenario_data.get("title", "未命名场景"),
            description=scenario_data.get("description", ""),
            context=scenario_data.get("context", ""),
            role=profile.role,
            language=profile.target_language
        )
        db.add(scenario)
        created_scenarios.append(scenario)

    db.commit()

    # 刷新获取完整数据
    for scenario in created_scenarios:
        db.refresh(scenario)

    return created_scenarios


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前会话的场景列表"""
    scenarios = db.query(Scenario).filter(
        Scenario.user_id == current_user.id
    ).order_by(Scenario.created_at.desc()).limit(20).all()

    return scenarios


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景详情"""
    scenario = db.query(Scenario).filter(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    ).first()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="场景不存在"
        )

    return scenario


@router.post("/{scenario_id}/select", response_model=MessageResponse)
async def select_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """选择场景"""
    # 先取消所有已选择的场景
    db.query(Scenario).filter(
        Scenario.user_id == current_user.id,
        Scenario.is_selected == True
    ).update({"is_selected": False})

    # 选择当前场景
    scenario = db.query(Scenario).filter(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    ).first()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="场景不存在"
        )

    scenario.is_selected = True
    db.commit()

    return MessageResponse(message="场景选择成功")


@router.delete("/{scenario_id}", response_model=MessageResponse)
async def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除场景"""
    scenario = db.query(Scenario).filter(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    ).first()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="场景不存在"
        )

    db.delete(scenario)
    db.commit()

    return MessageResponse(message="场景删除成功")
