from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import get_current_user, check_role

router = APIRouter(prefix="/books", tags=["books"])

@router.post("/add", dependencies=[Depends(check_role("operator"))])
def add_book(title: str, author: str, daily_price: float, db: Session = Depends(get_db)):
    book = models.Book(title=title, author=author, daily_price=daily_price)
    db.add(book)
    db.commit()
    return {"msg": "Book added"}

@router.get("/")
def list_books(db: Session = Depends(get_db)):
    return db.query(models.Book).all()