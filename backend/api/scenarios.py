import uuid
import asyncio
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.models.shared_scenario import SharedScenario
from backend.models.user_scenario import UserScenario
from backend.models.user_scenario_history import UserScenarioHistory
from backend.models.news_topic import NewsTopic
from backend.models.news_fetch_log import NewsFetchLog
from backend.models.news_topic_match import NewsTopicMatch
from backend.schemas import (
    ScenarioGenerate, ScenarioResponse, MessageResponse, ScenarioEnrichRequest,
    ScenarioDraftResponse, CustomScenarioCreate,
)
from backend.api.deps import get_current_user
from backend.services.llm_service import LLMService
from backend.services.news_service import NewsService, interest_key

router = APIRouter(prefix="/api/scenarios", tags=["场景"])

DEDUP_DAYS = 7  # 用户 N 天内见过的场景不重复出现


def _record_seen_scenarios(db: Session, user_id: int, scenario_ids: set[int]) -> None:
    """Persist views before replacing current scenario links during a refresh."""
    if not scenario_ids:
        return

    now = datetime.utcnow()
    history_rows = db.query(UserScenarioHistory).filter(
        UserScenarioHistory.user_id == user_id,
        UserScenarioHistory.shared_scenario_id.in_(scenario_ids),
    ).all()
    history_by_scenario_id = {row.shared_scenario_id: row for row in history_rows}
    for scenario_id in scenario_ids:
        history = history_by_scenario_id.get(scenario_id)
        if history:
            history.last_seen_at = now
        else:
            db.add(UserScenarioHistory(
                user_id=user_id,
                shared_scenario_id=scenario_id,
                last_seen_at=now,
            ))


def _profile_interests(profile: UserProfile) -> list[str]:
    try:
        return [item for item in json.loads(profile.news_interests or "[]") if isinstance(item, str)]
    except json.JSONDecodeError:
        return []


def _score_topic(topic: dict, role: str, interests: list[str]) -> int:
    text = " ".join([topic.get("headline", ""), topic.get("summary", "")]).lower()
    # Candidates were retrieved with role queries; direct community matches get extra priority.
    score = 70 + (15 if topic.get("source_type") == "community" and role in {"ai_engineer", "business_dev"} else 0)
    score += min(25, sum(12 for term in interests if term.lower() in text))
    score += min(20, sum(6 for term in NewsService().role_terms(role, None, []) if term.lower() in text))
    return min(score, 100)


async def _get_daily_news_topics(db: Session, profile: UserProfile, limit: int = 20) -> list[NewsTopic]:
    """Return a role/language/interest-specific daily evidence cache."""
    today, interests = datetime.utcnow().date(), _profile_interests(profile)
    key = interest_key(interests)
    cached = db.query(NewsTopic).join(NewsTopicMatch).filter(
        NewsTopicMatch.topic_date == today, NewsTopicMatch.role == profile.role,
        NewsTopicMatch.language == profile.target_language, NewsTopicMatch.interest_key == key,
    ).order_by(NewsTopicMatch.relevance_score.desc()).all()
    if cached:
        return cached[:limit]
    try:
        candidates = await asyncio.to_thread(NewsService().fetch_candidates, profile.role, profile.target_language, interests, profile.custom_role_name, limit)
        for candidate in candidates:
            evidence = await asyncio.to_thread(NewsService().extract_evidence, candidate)
            topic = db.query(NewsTopic).filter(NewsTopic.topic_date == today, NewsTopic.source_url == candidate["source_url"]).first()
            if not topic:
                topic = NewsTopic(topic_date=today, **candidate, extracted_text=evidence["extracted_text"], extraction_status=evidence["extraction_status"], evidence_json=json.dumps(evidence["evidence"], ensure_ascii=False))
                db.add(topic); db.flush()
            match = NewsTopicMatch(news_topic_id=topic.id, topic_date=today, role=profile.role, language=profile.target_language, interest_key=key, relevance_score=_score_topic(candidate, profile.role, interests), diversity_group=candidate.get("content_category"))
            db.add(match)
        db.commit()
    except Exception:
        db.rollback()
    return db.query(NewsTopic).join(NewsTopicMatch).filter(
        NewsTopicMatch.topic_date == today, NewsTopicMatch.role == profile.role,
        NewsTopicMatch.language == profile.target_language, NewsTopicMatch.interest_key == key,
        NewsTopicMatch.relevance_score >= 70,
    ).order_by(NewsTopicMatch.relevance_score.desc()).limit(limit).all()


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
        "last_active_sentence_id": us.last_active_sentence_id,
        "visibility": ss.visibility,
        "created_at": us.created_at,
    }


def _get_profile_or_400(db: Session, user_id: int) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先设置个人配置（角色和 target_language）")
    return profile


@router.post("/enrich", response_model=ScenarioDraftResponse)
async def enrich_scenario(
    data: ScenarioEnrichRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use the LLM to produce an editable draft without saving a scenario."""
    profile = _get_profile_or_400(db, current_user.id)
    try:
        draft = await asyncio.to_thread(
            LLMService().enrich_scenario,
            scenario_input=data.input.strip(),
            role=profile.role,
            custom_role_name=profile.custom_role_name,
            language=profile.target_language,
            proficiency_level=profile.proficiency_level,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"场景丰富失败：{exc}")

    title = str(draft.get("title", "")).strip()
    context = str(draft.get("context", "")).strip()
    if not title or not context:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="场景丰富失败：返回内容不完整")
    return {"title": title[:200], "description": str(draft.get("description", "")).strip()[:1000], "context": context[:4000]}


@router.post("/custom", response_model=ScenarioResponse)
async def create_custom_scenario(
    data: CustomScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a user-entered scenario, either private or reusable from the shared pool."""
    profile = _get_profile_or_400(db, current_user.id)
    raw_input = (data.raw_input or "").strip()
    context = (data.context or raw_input).strip()
    title = (data.title or raw_input[:50]).strip()
    description = (data.description or "").strip()
    if not title or not context:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请填写场景内容")

    scenario = SharedScenario(
        role=profile.role,
        language=profile.target_language,
        proficiency_level=profile.proficiency_level,
        title=title[:200],
        description=description[:1000],
        context=context[:4000],
        visibility=data.visibility,
        owner_user_id=current_user.id if data.visibility == "private" else None,
        is_custom=True,
    )
    try:
        db.add(scenario)
        db.flush()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已存在同名场景，请修改标题后重试")

    user_scenario = UserScenario(
        user_id=current_user.id,
        shared_scenario_id=scenario.id,
        session_id=str(uuid.uuid4()),
        is_selected=False,
    )
    db.add(user_scenario)
    db.commit()
    db.refresh(user_scenario)
    return _user_scenario_to_response(user_scenario)


@router.post("/generate", response_model=List[ScenarioResponse])
async def generate_scenarios(
    generate_data: ScenarioGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成 N 个口语场景（共享池复用 + 用户去重）"""
    profile = _get_profile_or_400(db, current_user.id)

    # Persist the current generated cards before replacing their links.  Reading
    # UserScenario alone is insufficient because refresh deletes those rows.
    active_generated_ids = {
        row.shared_scenario_id
        for row in db.query(UserScenario.shared_scenario_id).join(SharedScenario).filter(
            UserScenario.user_id == current_user.id,
            SharedScenario.is_custom == False,
        ).all()
    }
    _record_seen_scenarios(db, current_user.id, active_generated_ids)
    db.flush()

    # Query the durable viewing history instead of the soon-to-be-deleted links.
    cutoff = datetime.utcnow() - timedelta(days=DEDUP_DAYS)
    daily_topics = await _get_daily_news_topics(db, profile)
    seen_news_topic_ids = {
        topic_id
        for (topic_id,) in db.query(SharedScenario.news_topic_id).join(
            UserScenarioHistory,
            UserScenarioHistory.shared_scenario_id == SharedScenario.id,
        ).filter(
            UserScenarioHistory.user_id == current_user.id,
            UserScenarioHistory.last_seen_at >= cutoff,
            SharedScenario.news_topic_id.isnot(None),
        ).distinct().all()
    }
    available_topics = [topic for topic in daily_topics if topic.id not in seen_news_topic_ids]
    recent_ids = {
        row.shared_scenario_id
        for row in db.query(UserScenarioHistory.shared_scenario_id).filter(
            UserScenarioHistory.user_id == current_user.id,
            UserScenarioHistory.last_seen_at >= cutoff,
        ).all()
    }

    # 刷新仅替换 AI 生成的场景；用户创建的场景应持续保留在列表中。
    generated_scenario_ids = db.query(SharedScenario.id).filter(
        SharedScenario.is_custom == False
    )
    db.query(UserScenario).filter(
        UserScenario.user_id == current_user.id,
        UserScenario.shared_scenario_id.in_(generated_scenario_ids),
    ).delete(synchronize_session=False)
    db.commit()

    # 从共享池随机取该用户未见过的场景
    import sqlalchemy
    shared = db.query(SharedScenario).filter(
        SharedScenario.role == profile.role,
        SharedScenario.language == profile.target_language,
        SharedScenario.proficiency_level == profile.proficiency_level,
        SharedScenario.visibility == "shared",
        SharedScenario.news_topic_id.in_([topic.id for topic in available_topics]) if available_topics else SharedScenario.news_topic_id.is_(None),
        ~SharedScenario.id.in_(recent_ids) if recent_ids else True,
    ).order_by(sqlalchemy.func.random()).limit(generate_data.count).all()

    # 不够则调 LLM 补充
    if len(shared) < generate_data.count:
        used_topic_ids = {scenario.news_topic_id for scenario in shared}
        topics_to_generate = [topic for topic in available_topics if topic.id not in used_topic_ids]
        topics_to_generate = topics_to_generate[:generate_data.count - len(shared)]
        llm_service = LLMService()
        try:
            scenarios_data = await asyncio.to_thread(
                llm_service.generate_scenarios,
                role=profile.role,
                custom_role_name=profile.custom_role_name,
                language=profile.target_language,
                count=len(topics_to_generate) or generate_data.count,
                proficiency_level=profile.proficiency_level,
                news_topics=[{
                    "headline": topic.headline,
                    "summary": topic.summary or "",
                    "source": topic.source_name or "",
                    "evidence": json.loads(topic.evidence_json or "{}"),
                    "extracted_text": (topic.extracted_text or "")[:6000],
                } for topic in topics_to_generate],
            )
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"场景生成服务暂时不可用：{exc}",
            ) from exc

        if isinstance(scenarios_data, dict):
            scenarios_data = [scenarios_data]
        if not isinstance(scenarios_data, list):
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="场景生成服务返回了无效数据，请稍后重试",
            )

        scenarios_data = [item for item in scenarios_data if isinstance(item, dict)]
        if not scenarios_data:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="场景生成服务未返回有效场景，请稍后重试",
            )

        existing_titles = {s.title for s in shared}
        for index, sd in enumerate(scenarios_data):
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
                news_topic_id=topics_to_generate[index].id if index < len(topics_to_generate) else None,
            )
            try:
                # A savepoint prevents one duplicate title from rolling back
                # other newly generated scenarios in this refresh.
                with db.begin_nested():
                    db.add(ss)
                    db.flush()
                shared.append(ss)
                existing_titles.add(title)
            except IntegrityError:
                # Do not fall back to an existing title here: it may belong to
                # the user's recent history and would defeat refresh de-duplication.
                continue
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

    _record_seen_scenarios(
        db,
        current_user.id,
        {us.shared_scenario_id for us in user_scenarios},
    )
    db.commit()

    # 同一批场景的 created_at 可能相同；用 ID 作为次级排序，确保新建的场景稳定显示在最上方。
    custom_user_scenarios = db.query(UserScenario).join(SharedScenario).filter(
        UserScenario.user_id == current_user.id,
        SharedScenario.is_custom == True,
    ).all()
    all_user_scenarios = user_scenarios + custom_user_scenarios
    all_user_scenarios.sort(key=lambda us: (us.created_at, us.id), reverse=True)
    return [_user_scenario_to_response(us) for us in all_user_scenarios]


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的场景列表"""
    user_scenarios = db.query(UserScenario).filter(
        UserScenario.user_id == current_user.id
    ).order_by(UserScenario.created_at.desc(), UserScenario.id.desc()).limit(20).all()
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

    # A private scenario has no other legitimate user association; clean up its
    # backing record (and any generated sentences) with the association.
    shared = us.shared_scenario
    db.delete(us)
    if shared.visibility == "private" and shared.owner_user_id == current_user.id:
        db.delete(shared)
    db.commit()
    return MessageResponse(message="场景删除成功")
