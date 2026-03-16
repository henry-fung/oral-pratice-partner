from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.models.scenario import Scenario
from backend.models.sentence import Sentence
from backend.schemas import SentenceGenerate, SentenceResponse, SentenceComplete, MessageResponse
from backend.api.deps import get_current_user
from backend.services.llm_service import LLMService

router = APIRouter(prefix="/api/sentences", tags=["句子"])


@router.post("/generate", response_model=SentenceResponse)
async def generate_sentence(
    generate_data: SentenceGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成场景下的一句话"""
    # 获取场景
    scenario = db.query(Scenario).filter(
        Scenario.id == generate_data.scenario_id,
        Scenario.user_id == current_user.id
    ).first()

    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="场景不存在"
        )

    # 获取用户配置
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先设置个人配置"
        )

    # 调用 LLM 生成句子
    llm_service = LLMService()
    sentence_data = llm_service.generate_sentence(
        scenario={
            "title": scenario.title,
            "description": scenario.description,
            "context": scenario.context
        },
        role=profile.role,
        language=profile.target_language,
        native_language=profile.native_language,
        proficiency_level=profile.proficiency_level
    )

    # 计算句子顺序
    max_order = db.query(Sentence).filter(
        Sentence.scenario_id == scenario.id
    ).count()

    # 保存到数据库
    new_sentence = Sentence(
        scenario_id=scenario.id,
        native_text=sentence_data.get("native", ""),
        target_text=sentence_data.get("target", ""),
        pronunciation_guide=sentence_data.get("pronunciation", ""),
        sentence_order=max_order + 1
    )
    db.add(new_sentence)
    db.commit()
    db.refresh(new_sentence)

    return new_sentence


@router.get("/{sentence_id}", response_model=SentenceResponse)
async def get_sentence(
    sentence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取句子详情"""
    sentence = db.query(Sentence).join(Scenario).filter(
        Sentence.id == sentence_id,
        Scenario.user_id == current_user.id
    ).first()

    if not sentence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="句子不存在"
        )

    return sentence


@router.post("/{sentence_id}/complete", response_model=MessageResponse)
async def complete_sentence(
    sentence_id: int,
    complete_data: SentenceComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记句子练习完成"""
    sentence = db.query(Sentence).join(Scenario).filter(
        Sentence.id == sentence_id,
        Scenario.user_id == current_user.id
    ).first()

    if not sentence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="句子不存在"
        )

    sentence.is_completed = True
    if complete_data.user_attempt:
        sentence.user_attempt = complete_data.user_attempt

    db.commit()

    return MessageResponse(message="练习完成！")


@router.get("/scenario/{scenario_id}/next", response_model=Optional[SentenceResponse])
async def get_next_sentence(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景下的下一句话（如果已存在则返回，否则返回 null 让前端调用 generate）"""
    # 查找该场景下最新的未完成的句子
    sentence = db.query(Sentence).join(Scenario).filter(
        Sentence.scenario_id == scenario_id,
        Scenario.user_id == current_user.id
    ).order_by(Sentence.sentence_order.desc()).first()

    # 如果句子超过 5 句，返回 None 表示场景完成
    if sentence and sentence.sentence_order >= 5:
        return None

    return sentence


@router.get("/scenario/{scenario_id}/list", response_model=List[SentenceResponse])
async def list_scenario_sentences(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景下的所有句子"""
    sentences = db.query(Sentence).join(Scenario).filter(
        Sentence.scenario_id == scenario_id,
        Scenario.user_id == current_user.id
    ).order_by(Sentence.sentence_order).all()

    return sentences
