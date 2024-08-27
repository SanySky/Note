from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
import httpx
import bcrypt
import jwt
from datetime import datetime, timedelta

from auth import get_current_user, get_db, SECRET_KEY, ALGORITHM
from models import User, Note

app = FastAPI()


# Ваши модели Pydantic
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


# Функция для создания JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/register/", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(username=user.username, hashed_password=hashed_password.decode('utf-8'))

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse(username=db_user.username)


@app.post("/login/")
async def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/notes/", response_model=NoteResponse)
async def create_note(note: NoteCreate, current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    # Проверка орфографии с Яндекс.Спелле
    async with httpx.AsyncClient() as client:
        response = await client.post("https://speller.yandex.net/services/spellservice.json/checkText", data={"text": note.content})
    errors = response.json()
    if errors:
        raise HTTPException(status_code=400, detail="Spelling errors found")

    db_note = Note(content=note.content, user_id=current_user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return NoteResponse(id=db_note.id, user_id=current_user.id, content=db_note.content)


@app.get("/notes/", response_model=List[NoteResponse])
async def read_notes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.user_id == current_user.id).all()
    return [NoteResponse(id=note.id, user_id=note.user_id, content=note.content) for note in notes]
