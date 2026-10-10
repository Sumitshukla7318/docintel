"""
User + Workspace models.

Multi-tenancy model: every User belongs to exactly one Workspace (their
tenant). All documents, agents, and chat sessions are scoped by workspace_id
so users only ever see their own org's data. Roles are scoped per-workspace
(owner/admin/member) so this also supports team accounts later.
"""
import enum
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    OWNER = "owner"      # created the workspace, full control
    ADMIN = "admin"      # can manage docs/users within workspace
    MEMBER = "member"    # can query + upload, no user management


class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.MEMBER)

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    workspace: Mapped["Workspace"] = relationship(back_populates="users")