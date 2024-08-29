from typing import List
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="owner")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    owner: Mapped[User] = relationship("User", back_populates="notes")


class NoteCreate(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    user_id: int
    content: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
