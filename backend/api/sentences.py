import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.models.user_scenario import UserScenario
from backend.models.shared_scenario import SharedScenario
from backend.models.shared_sentence import SharedSentence
from backend.models.user_sentence_progress import UserSentenceProgress
from backend.schemas import SentenceGenerate, SentenceResponse, SentenceComplete, MessageResponse, ContinueRequest
from backend.api.deps import get_current_user
from backend.services.llm_service import LLMService

router = APIRouter(prefix="/api/sentences", tags=["句子"])

MAX_SENTENCES_PER_SCENARIO = 5


def _sentence_to_response(ss: SharedSentence, progress: Optional[UserSentenceProgress]) -> dict:
    return {
        "id": ss.id,
        "scenario_id": ss.shared_scenario_id,
        "native_text": ss.native_text,
        "target_text": ss.target_text,
        "pronunciation_guide": ss.pronunciation_guide,
        "difficulty_level": ss.difficulty_level,
        "sentence_order": ss.sentence_order,
        "is_completed": progress.is_completed if progress else False,
        "context_text": ss.context_text,
        "context_native": ss.context_native,
    }


def _get_user_scenario(db: Session, scenario_id: int, user_id: int) -> UserScenario:
    us = db.query(UserScenario).filter(
        UserScenario.id == scenario_id,
        UserScenario.user_id == user_id,
    ).first()
    if not us:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="场景不存在")
    return us


def _get_progress(db: Session, user_id: int, sentence_id: int) -> Optional[UserSentenceProgress]:
    return db.query(UserSentenceProgress).filter(
        UserSentenceProgress.user_id == user_id,
        UserSentenceProgress.shared_sentence_id == sentence_id,
    ).first()


def _completed_ids(db: Session, user_id: int, shared_scenario_id: int) -> set:
    rows = db.query(UserSentenceProgress.shared_sentence_id).join(
        SharedSentence,
        SharedSentence.id == UserSentenceProgress.shared_sentence_id
    ).filter(
        UserSentenceProgress.user_id == user_id,
        UserSentenceProgress.is_completed == True,
        SharedSentence.shared_scenario_id == shared_scenario_id,
    ).all()
    return {r[0] for r in rows}


def _prefetch_next_sentence(shared_scenario_id: int, profile_data: dict):
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        ss = db.query(SharedScenario).filter(SharedScenario.id == shared_scenario_id).first()
        if not ss:
            return
        count = db.query(SharedSentence).filter(
            SharedSentence.shared_scenario_id == shared_scenario_id,
            SharedSentence.parent_sentence_id == None,
        ).count()
        if count >= MAX_SENTENCES_PER_SCENARIO:
            return
        llm_service = LLMService()
        sentence_data = llm_service.generate_sentence(
            scenario={"title": ss.title, "description": ss.description, "context": ss.context},
            role=profile_data["role"],
            language=profile_data["target_language"],
            native_language=profile_data["native_language"],
            proficiency_level=profile_data["proficiency_level"],
        )
        db.add(SharedSentence(
            shared_scenario_id=shared_scenario_id,
            native_text=sentence_data.get("native", ""),
            target_text=sentence_data.get("target", ""),
            pronunciation_guide=sentence_data.get("pronunciation", ""),
            sentence_order=count + 1,
        ))
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


@router.post("/generate", response_model=SentenceResponse)
async def generate_sentence(
    generate_data: SentenceGenerate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取或生成场景下的下一句话"""
    us = _get_user_scenario(db, generate_data.scenario_id, current_user.id)
    shared_scenario_id = us.shared_scenario_id

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先设置个人配置")

    done_ids = _completed_ids(db, current_user.id, shared_scenario_id)

    # 只取根句，按 continuation 子链数量倒序优先
    child_counts = (
        db.query(
            SharedSentence.parent_sentence_id.label("pid"),
            func.count().label("cnt")
        )
        .filter(SharedSentence.shared_scenario_id == shared_scenario_id)
        .filter(SharedSentence.parent_sentence_id != None)
        .group_by(SharedSentence.parent_sentence_id)
        .subquery()
    )
    sentence = (
        db.query(SharedSentence)
        .outerjoin(child_counts, SharedSentence.id == child_counts.c.pid)
        .filter(SharedSentence.shared_scenario_id == shared_scenario_id)
        .filter(SharedSentence.parent_sentence_id == None)
        .filter(~SharedSentence.id.in_(done_ids) if done_ids else True)
        .order_by(func.coalesce(child_counts.c.cnt, 0).desc(), SharedSentence.sentence_order)
        .first()
    )

    if not sentence:
        # 共享池里没有可用根句，LLM 生成
        total = db.query(SharedSentence).filter(
            SharedSentence.shared_scenario_id == shared_scenario_id,
            SharedSentence.parent_sentence_id == None,
        ).count()
        if total >= MAX_SENTENCES_PER_SCENARIO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该场景练习已完成")

        shared_scenario = db.query(SharedScenario).filter(SharedScenario.id == shared_scenario_id).first()
        llm_service = LLMService()
        sentence_data = await asyncio.to_thread(
            llm_service.generate_sentence,
            scenario={"title": shared_scenario.title, "description": shared_scenario.description, "context": shared_scenario.context},
            role=profile.role,
            language=profile.target_language,
            native_language=profile.native_language,
            proficiency_level=profile.proficiency_level,
        )
        sentence = SharedSentence(
            shared_scenario_id=shared_scenario_id,
            native_text=sentence_data.get("native", ""),
            target_text=sentence_data.get("target", ""),
            pronunciation_guide=sentence_data.get("pronunciation", ""),
            sentence_order=total + 1,
        )
        db.add(sentence)
        db.commit()
        db.refresh(sentence)

    progress = _get_progress(db, current_user.id, sentence.id)

    # 预生成下一句（只统计根句）
    total_now = db.query(SharedSentence).filter(
        SharedSentence.shared_scenario_id == shared_scenario_id,
        SharedSentence.parent_sentence_id == None,
    ).count()
    if total_now < MAX_SENTENCES_PER_SCENARIO:
        profile_data = {
            "role": profile.role,
            "target_language": profile.target_language,
            "native_language": profile.native_language,
            "proficiency_level": profile.proficiency_level,
        }
        background_tasks.add_task(_prefetch_next_sentence, shared_scenario_id, profile_data)

    return _sentence_to_response(sentence, progress)


@router.post("/continue", response_model=SentenceResponse)
async def continue_conversation(
    data: ContinueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """继续对话：复用或生成当前句的 continuation"""
    us = _get_user_scenario(db, data.scenario_id, current_user.id)
    sentence = db.query(SharedSentence).filter(SharedSentence.id == data.sentence_id).first()
    if not sentence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="句子不存在")

    done_ids = _completed_ids(db, current_user.id, us.shared_scenario_id)
    continuation = (
        db.query(SharedSentence)
        .filter(SharedSentence.parent_sentence_id == data.sentence_id)
        .filter(~SharedSentence.id.in_(done_ids) if done_ids else True)
        .first()
    )

    if not continuation:
        shared_scenario = db.query(SharedScenario).filter(SharedScenario.id == us.shared_scenario_id).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先设置个人配置")
        llm_service = LLMService()
        result = await asyncio.to_thread(
            llm_service.generate_continuation,
            scenario={"title": shared_scenario.title, "description": shared_scenario.description, "context": shared_scenario.context},
            previous_target=sentence.target_text,
            role=profile.role,
            language=profile.target_language,
            proficiency_level=profile.proficiency_level,
        )
        continuation = SharedSentence(
            shared_scenario_id=us.shared_scenario_id,
            parent_sentence_id=data.sentence_id,
            context_text=result.get("context", ""),
            context_native=result.get("context_native", ""),
            native_text=result.get("native", ""),
            target_text=result.get("target", ""),
            sentence_order=0,
        )
        db.add(continuation)
        db.commit()
        db.refresh(continuation)

    progress = _get_progress(db, current_user.id, continuation.id)
    return _sentence_to_response(continuation, progress)


@router.get("/{sentence_id}", response_model=SentenceResponse)
async def get_sentence(
    sentence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取句子详情"""
    sentence = db.query(SharedSentence).join(
        UserScenario,
        and_(
            UserScenario.shared_scenario_id == SharedSentence.shared_scenario_id,
            UserScenario.user_id == current_user.id,
        )
    ).filter(SharedSentence.id == sentence_id).first()

    if not sentence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="句子不存在")

    progress = _get_progress(db, current_user.id, sentence_id)
    return _sentence_to_response(sentence, progress)


@router.post("/{sentence_id}/complete", response_model=MessageResponse)
async def complete_sentence(
    sentence_id: int,
    complete_data: SentenceComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记句子练习完成"""
    # Verify user has access to this sentence
    sentence = db.query(SharedSentence).join(
        UserScenario,
        and_(
            UserScenario.shared_scenario_id == SharedSentence.shared_scenario_id,
            UserScenario.user_id == current_user.id,
        )
    ).filter(SharedSentence.id == sentence_id).first()

    if not sentence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="句子不存在")

    progress = _get_progress(db, current_user.id, sentence_id)
    if not progress:
        progress = UserSentenceProgress(
            user_id=current_user.id,
            shared_sentence_id=sentence_id,
        )
        db.add(progress)

    progress.is_completed = True
    if complete_data.user_attempt:
        progress.user_attempt = complete_data.user_attempt
    db.commit()
    return MessageResponse(message="练习完成！")


@router.get("/scenario/{scenario_id}/next", response_model=Optional[SentenceResponse])
async def get_next_sentence(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景下的下一句话（已存在则返回，否则返回 null）"""
    us = _get_user_scenario(db, scenario_id, current_user.id)
    shared_scenario_id = us.shared_scenario_id

    done_ids = _completed_ids(db, current_user.id, shared_scenario_id)
    total = db.query(SharedSentence).filter(SharedSentence.shared_scenario_id == shared_scenario_id).count()

    if total >= MAX_SENTENCES_PER_SCENARIO and len(done_ids) >= MAX_SENTENCES_PER_SCENARIO:
        return None

    sentence = db.query(SharedSentence).filter(
        SharedSentence.shared_scenario_id == shared_scenario_id,
        ~SharedSentence.id.in_(done_ids) if done_ids else True,
    ).order_by(SharedSentence.sentence_order).first()

    if not sentence:
        return None

    progress = _get_progress(db, current_user.id, sentence.id)
    return _sentence_to_response(sentence, progress)


@router.get("/scenario/{scenario_id}/list", response_model=List[SentenceResponse])
async def list_scenario_sentences(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取场景下的所有句子"""
    us = _get_user_scenario(db, scenario_id, current_user.id)
    shared_scenario_id = us.shared_scenario_id

    sentences = db.query(SharedSentence).filter(
        SharedSentence.shared_scenario_id == shared_scenario_id
    ).order_by(SharedSentence.sentence_order).all()

    result = []
    for s in sentences:
        progress = _get_progress(db, current_user.id, s.id)
        result.append(_sentence_to_response(s, progress))
    return result
