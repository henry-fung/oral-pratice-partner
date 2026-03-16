from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# === 用户相关 Schemas ===
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithToken(UserResponse):
    access_token: str


# === 用户配置相关 Schemas ===
class UserProfileCreate(BaseModel):
    role: str
    custom_role_name: Optional[str] = None
    target_language: str
    native_language: Optional[str] = "zh"
    proficiency_level: Optional[str] = "intermediate"


class UserProfileUpdate(BaseModel):
    role: Optional[str] = None
    custom_role_name: Optional[str] = None
    target_language: Optional[str] = None
    native_language: Optional[str] = None
    proficiency_level: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    role: str
    custom_role_name: Optional[str] = None
    target_language: str
    native_language: str
    proficiency_level: str
    created_at: datetime

    class Config:
        from_attributes = True


# === 场景相关 Schemas ===
class ScenarioGenerate(BaseModel):
    count: int = 5


class ScenarioSelect(BaseModel):
    pass  # 空 body，仅用于 POST 请求


class ScenarioResponse(BaseModel):
    id: int
    user_id: int
    session_id: str
    title: str
    description: Optional[str] = None
    context: Optional[str] = None
    role: str
    language: str
    is_selected: bool
    created_at: datetime

    class Config:
        from_attributes = True


# === 句子相关 Schemas ===
class SentenceGenerate(BaseModel):
    scenario_id: int


class SentenceComplete(BaseModel):
    user_attempt: Optional[str] = None


class SentenceResponse(BaseModel):
    id: int
    scenario_id: int
    native_text: str
    target_text: str
    pronunciation_guide: Optional[str] = None
    difficulty_level: str
    sentence_order: int
    is_completed: bool

    class Config:
        from_attributes = True


# === 单词本相关 Schemas ===
class VocabularyLookup(BaseModel):
    word: str
    language: str


class VocabularyCreate(BaseModel):
    word: str
    language: str
    definition: Optional[str] = None
    example_sentence: Optional[str] = None
    pronunciation: Optional[str] = None
    added_from_sentence_id: Optional[int] = None


class VocabularyResponse(BaseModel):
    id: int
    user_id: int
    word: str
    language: str
    definition: Optional[str] = None
    example_sentence: Optional[str] = None
    pronunciation: Optional[str] = None
    is_mastered: bool
    review_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# === 通用响应 ===
class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
