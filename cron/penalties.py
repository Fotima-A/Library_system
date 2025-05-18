from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from datetime import datetime
from utils import calculate_penalty

scheduler = BackgroundScheduler()

@scheduler.scheduled_job("interval", hours=1)
def check_late_orders():
    db: Session = SessionLocal()
    now = datetime.utcnow()

    orders = db.query(models.Order).filter(models.Order.return_date == None, models.Order.due_date < now, models.Order.status == "borrowed").all()
    for order in orders:
        book = db.query(models.Book).filter_by(id=order.book_id).first()
        if book:
            order.penalty = calculate_penalty(order.due_date, now, book.daily_price)
            db.add(order)

    reserves = db.query(models.Order).filter(models.Order.status == "reserved", models.Order.due_date < now).all()
    for reserve in reserves:
        reserve.status = "cancelled"
        db.add(reserve)

    db.commit()
    db.close()