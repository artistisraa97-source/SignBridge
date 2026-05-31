from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_verified = Column(Boolean, nullable=False, server_default='0')
    verification_code = Column(String(128), nullable=True)
    verification_expires = Column(DateTime(timezone=True), nullable=True)

    # Active users are stored here once email verification completes.


class PendingUser(Base):
    __tablename__ = 'pending_users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    verification_code = Column(String(128), nullable=False)
    verification_expires = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Pending users remain here until verification completes.
