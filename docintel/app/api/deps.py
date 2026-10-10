"""
Reusable FastAPI dependencies:
- get_current_user: decodes + validates the bearer access token
- require_role: factory for RBAC-gated endpoints
- get_workspace_id: convenience dependency for scoping queries
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import InvalidTokenError, TokenType, decode_token_of_type
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_id

# HTTPBearer makes Swagger's "Authorize" button show a plain token field —
# matches how our API actually issues tokens (via JSON login/register, not
# OAuth2 form-encoded password grant).
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_token_of_type(credentials.credentials, TokenType.ACCESS)
    except InvalidTokenError:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for RBAC. Usage:
        @router.delete(..., dependencies=[Depends(require_role(UserRole.OWNER, UserRole.ADMIN))])
    """
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return checker


async def get_workspace_id(current_user: User = Depends(get_current_user)) -> uuid.UUID:
    """Every workspace-scoped query/service call should depend on this, never trust a client-supplied workspace_id."""
    return current_user.workspace_id