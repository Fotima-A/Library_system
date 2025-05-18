from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
from passlib.context import CryptContext
import jwt, datetime

router = APIRouter(prefix="/auth", tags=["auth"])
SECRET_KEY = "secret"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/signup")
def signup(username: str, password: str, role: str, db: Session = Depends(get_db)):
    user = models.User(username=username, password=pwd_context.hash(password), role=role)
    db.add(user)
    db.commit()
    return {"msg": "User registered"}

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = jwt.encode({"sub": user.id, "role": user.role, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token}
