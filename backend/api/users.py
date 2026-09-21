import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.schemas import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from backend.api.deps import get_current_user


def _normalize_interests(values):
    return [value.strip()[:60] for value in (values or []) if value and value.strip()][:10]


def _profile_response(profile):
    payload = {column.name: getattr(profile, column.name) for column in profile.__table__.columns}
    try:
        payload["news_interests"] = json.loads(profile.news_interests or "[]")
    except json.JSONDecodeError:
        payload["news_interests"] = []
    return payload

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户配置"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未设置个人配置"
        )

    return _profile_response(profile)


@router.post("/profile", response_model=UserProfileResponse)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户配置"""
    # 检查是否已存在配置
    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="配置已存在，请使用 PUT 方法更新"
        )

    new_profile = UserProfile(
        user_id=current_user.id,
        role=profile_data.role,
        custom_role_name=profile_data.custom_role_name,
        target_language=profile_data.target_language,
        native_language=profile_data.native_language,
        proficiency_level=profile_data.proficiency_level,
        news_interests=json.dumps(_normalize_interests(profile_data.news_interests), ensure_ascii=False),
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return _profile_response(new_profile)


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户配置"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未设置个人配置"
        )

    # 更新字段
    if profile_data.role is not None:
        profile.role = profile_data.role
    if profile_data.custom_role_name is not None:
        profile.custom_role_name = profile_data.custom_role_name
    if profile_data.target_language is not None:
        profile.target_language = profile_data.target_language
    if profile_data.native_language is not None:
        profile.native_language = profile_data.native_language
    if profile_data.proficiency_level is not None:
        profile.proficiency_level = profile_data.proficiency_level
    if profile_data.news_interests is not None:
        profile.news_interests = json.dumps(_normalize_interests(profile_data.news_interests), ensure_ascii=False)

    db.commit()
    db.refresh(profile)

    return _profile_response(profile)
