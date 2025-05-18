from celery_app import celery_app
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Order, OrderStatus
from datetime import datetime, timedelta

@celery_app.task
def cancel_expired_orders():
    db: Session = SessionLocal()
    try:
        orders = db.query(Order).filter(Order.status == OrderStatus.booked).all()
        now = datetime.now()

        for order in orders:
            if order.booked_at + timedelta(days=1) < now:
                order.status = OrderStatus.cancelled
                print(f"Order {order.id} cancelled due to timeout.")
        db.commit()
    finally:
        db.close()
