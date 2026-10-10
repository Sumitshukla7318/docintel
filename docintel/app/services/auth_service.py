"""
Auth business logic, kept separate from the router so it's independently
testable and reusable (e.g. from a future admin CLI or seed script).
"""
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole, Workspace
from app.schemas.auth import UserLogin, UserRegister


class AuthError(Exception):
    """Raised for any auth failure the router should turn into a 4xx."""
    pass


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "workspace"


async def register_user(db: AsyncSession, payload: UserRegister) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise AuthError("A user with this email already exists")

    # Ensure workspace slug uniqueness by appending a short suffix on collision
    base_slug = _slugify(payload.workspace_name)
    slug = base_slug
    suffix = 1
    while (await db.execute(select(Workspace).where(Workspace.slug == slug))).scalar_one_or_none():
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    workspace = Workspace(name=payload.workspace_name, slug=slug)
    db.add(workspace)
    await db.flush()  # get workspace.id without committing yet

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.OWNER,  # first user of a new workspace is its owner
        workspace_id=workspace.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, payload: UserLogin) -> User:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Invalid email or password")

    if not user.is_active:
        raise AuthError("This account has been deactivated")

    return user


def issue_tokens(user: User) -> tuple[str, str]:
    access = create_access_token(
        user_id=str(user.id), role=user.role.value, workspace_id=str(user.workspace_id)
    )
    refresh = create_refresh_token(user_id=str(user.id))
    return access, refresh


async def get_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()