from fastapi import FastAPI, Depends, HTTPException, status, Path, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from auth import get_db
from models import User, Book, Order, OrderStatus, UserRole
from schemas import UserCreate, UserResponse, BookCreate, BookResponse, OrderCreate, OrderResponse, OrderAddRating
from database import SessionLocal, engine, Base
from dependencies import get_current_user, require_roles


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
Base.metadata.create_all(bind=engine)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post( "/register", response_model=UserResponse )
def register_user(user: UserCreate, db: Session = Depends( get_db )):
    existing_user = db.query( User ).filter( User.username == user.username ).first()
    if existing_user:
        raise HTTPException( status_code=400, detail="Username already registered" )

    hashed_password = get_password_hash( user.password )
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add( db_user )
    db.commit()
    db.refresh( db_user )
    return db_user


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin))):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Kitoblar
@app.post("/books/", response_model=BookResponse)
def create_book(book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin, UserRole.operator))):
    db_book = Book(title=book.title, daily_price=book.daily_price, author=book.author)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[BookResponse])
def list_books(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin, UserRole.operator, UserRole.user))):
    return db.query(Book).all()

@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin, UserRole.operator))):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    db_book.title = book.title
    db_book.daily_price = book.daily_price
    db_book.author = book.author
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin, UserRole.operator))):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return {"detail": "Book deleted"}

@app.post("/orders/", response_model=OrderResponse)
def book_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.user))
):
    db_book = db.query(Book).filter(Book.id == order.book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing_order = db.query(Order).filter(
        Order.book_id == order.book_id,
        Order.user_id == current_user.id,
        Order.status.in_([OrderStatus.booked, OrderStatus.taken])
    ).first()
    if existing_order:
        raise HTTPException(status_code=400, detail="You already booked.")
    new_order = Order(
        user_id=current_user.id,
        book_id=order.book_id,
        status=OrderStatus.booked,
        booked_at=datetime.utcnow()
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.get("/orders/", response_model=List[OrderResponse])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.admin, UserRole.operator))):
    orders = db.query(Order).options(joinedload(Order.user), joinedload(Order.book)).all()
    return orders


@app.put("/orders/{order_id}/accept", response_model=OrderResponse)
def accept_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin))
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.booked:
        raise HTTPException(status_code=400, detail="Order cannot be accepted")
    order.status = OrderStatus.taken
    order.taken_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order

@app.put("/orders/{order_id}/return", response_model=OrderResponse)
def return_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in [OrderStatus.booked, OrderStatus.taken]:
        raise HTTPException(status_code=400, detail="Order cannot be returned")

    order.status = OrderStatus.returned
    order.returned_at = datetime.utcnow()


    if order.taken_at and order.returned_at:
        days = (order.returned_at - order.taken_at).days
        if days > 1:
            penalty_days = days - 1
            order.penalty = penalty_days * order.book.daily_price * 1.5

    db.commit()
    db.refresh(order)
    return order

@app.put("/orders/{order_id}/rate", response_model=OrderResponse)
def rate_order(order_id: int, rating_data: OrderAddRating, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.user))):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.returned:
        raise HTTPException(status_code=400, detail="You can only rate returned books")
    if rating_data.rating < 0 or rating_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 0 and 5")
    order.rating = rating_data.rating
    db.commit()
    db.refresh(order)
    return order
