from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database import get_db, User
from auth import get_current_user, get_current_admin, get_password_hash

router = APIRouter(prefix="/api/users", tags=["用户管理"])


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"  # admin or user


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（仅管理员）"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else None
        )
        for u in users
    ]


@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建新用户（仅管理员）"""
    # Check if username already exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # Validate role
    if user_data.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色必须是 admin 或 user"
        )
    
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() if new_user.created_at else None
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除管理员账户"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "用户已删除", "code": 200}
