from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.profile import UserProfile
from backend.schemas import UserCreate, UserLogin, UserWithToken, UserResponse, UserProfileResponse, MessageResponse, TokenResponse
from backend.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
import os

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserWithToken)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 生成 JWT token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "username": new_user.username},
        expires_delta=timedelta(days=7)
    )

    return UserWithToken(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        access_token=access_token
    )


@router.post("/login", response_model=UserWithToken)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查账户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    # 生成 JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(days=7)
    )

    return UserWithToken(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        access_token=access_token
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # 占位，实际认证在依赖注入中实现
):
    """获取当前用户信息"""
    # 这个端点需要 JWT 认证依赖注入，稍后完善
    raise HTTPException(status_code=501, detail="功能实现中")


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """用户登出（客户端删除 token 即可）"""
    return MessageResponse(message="登出成功")
