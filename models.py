from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"
    user = "user"

class OrderStatus(str, enum.Enum):
    booked = "booked"
    taken = "taken"
    returned = "returned"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.user)

    orders = relationship("Order", back_populates="user")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    daily_price = Column(Integer)
    author = Column(String, nullable=True)

    orders = relationship("Order", back_populates="book")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    status = Column(Enum(OrderStatus), default=OrderStatus.booked)
    booked_at = Column(DateTime, default=datetime.utcnow)
    taken_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)
    penalty = Column(Float, default=0.0)

    user = relationship("User", back_populates="orders")
    book = relationship("Book", back_populates="orders")
