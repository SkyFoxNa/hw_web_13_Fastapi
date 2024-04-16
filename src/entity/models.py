import enum
from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Integer, ForeignKey, DateTime, func, Enum, Boolean
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(primary_key = True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False, index = True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False,  index = True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, index = True)
    phone_number: Mapped[str] = mapped_column(String(20), index = True)
    birthday: Mapped[Date] = mapped_column(Date, nullable=False)
    address: Mapped[str] = mapped_column(String(250))
    notes: Mapped[str] = mapped_column(String(250))
    interests: Mapped[str] = mapped_column(String(250))
    is_active: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[date] = mapped_column('created_at', DateTime, default = func.now(), nullable = True)
    updated_at: Mapped[date] = mapped_column('updated_at', DateTime, default = func.now(), onupdate = func.now(),
                                             nullable = True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable = True)
    user: Mapped["User"] = relationship("User", backref = "contacts", lazy = "joined")


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column('created_at', DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    role: Mapped[Enum] = mapped_column('role', Enum(Role), default = Role.user, nullable = True)
    verified: Mapped[bool] = mapped_column(Boolean, default = False, nullable = True)
