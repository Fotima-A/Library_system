from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import enum
from models import UserRole, OrderStatus

class UserRole(str, enum.Enum):
    admin = "admin"
    operator = "operator"
    user = "user"

class OrderStatus(str, enum.Enum):
    booked = "booked"
    taken = "taken"
    returned = "returned"
    cancelled = "cancelled"

class UserBase(BaseModel):
    username: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.user

class UserResponse(UserBase):
    id: int
    role: UserRole
    class Config:
        orm_mode = True

class BookBase(BaseModel):
    title: str
    daily_price: int
    author: Optional[str]

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    user_id: int
    book_id: int

class OrderCreate(BaseModel):
    book_id: int


class OrderUpdateStatus(BaseModel):
    status: OrderStatus

class OrderAddRating(BaseModel):
    rating: int  # 0 to 5

class OrderResponse(OrderBase):
    id: int
    status: OrderStatus
    booked_at: datetime
    taken_at: Optional[datetime]
    returned_at: Optional[datetime]
    rating: Optional[int]
    penalty: float
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class OrderCreate(BaseModel):
    book_id: int

class OrderAddRating(BaseModel):
    rating: int = Field(..., ge=0, le=5)
class OrderResponse(BaseModel):
    id: int
    user: UserResponse
    book: Optional[BookResponse]
    status: OrderStatus
    booked_at: datetime
    taken_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    rating: Optional[int] = None
    penalty: float = 0.0

    class Config:
        orm_mode = True


