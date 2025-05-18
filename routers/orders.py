from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
import models
from auth import get_current_user, check_role

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/reserve/{book_id}", dependencies=[Depends(check_role("user"))])
def reserve(book_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    now = datetime.utcnow()
    order = models.Order(user_id=current_user.id, book_id=book_id, reserved_at=now, due_date=now + timedelta(days=1), status="reserved")
    db.add(order)
    db.commit()
    return {"msg": "Book reserved"}

@router.post("/rate/{order_id}")
def rate(order_id: int, rating: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    order = db.query(models.Order).filter_by(id=order_id, user_id=current_user.id).first()
    if not order or order.status not in ["borrowed", "returned"]:
        raise HTTPException(status_code=400, detail="Cannot rate this order")
    order.rating = rating
    db.commit()
    return {"msg": "Rated successfully"}