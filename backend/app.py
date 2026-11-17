import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database import Base, engine, ensure_compatibility_columns, get_db
from models import Cart, CartItem, Order, OrderItem, Product, User
from schemas import (
    AuthResponse,
    CartItemRequest,
    CartItemUpdate,
    CartResponse,
    LoginRequest,
    OrderResponse,
    ProductCreate,
    ProductResponse,
    SignupRequest,
    UserResponse,
)


SERVICE_ROLE = os.getenv("SERVICE_ROLE", "all")
JWT_SECRET = os.getenv("JWT_SECRET", "local-development-secret-change-me")
JWT_ALGORITHM = "HS256"

SEED_PRODUCTS = (
    {
        "name": "Gateway Demo Jacket",
        "brand": "Gateway",
        "description": "A lightweight everyday jacket with a clean, versatile silhouette.",
        "price": Decimal("1299.00"),
        "category": "Clothing",
        "stock_quantity": 20,
        "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Canvas Backpack",
        "brand": "Gateway",
        "description": "A durable canvas backpack with room for daily essentials.",
        "price": Decimal("899.00"),
        "category": "Bags",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80",
    },
    {
        "name": "Silhouette Seed",
        "brand": "Gateway",
        "description": "A small decorative keepsake designed to brighten a workspace.",
        "price": Decimal("1499.00"),
        "category": "Accessories",
        "stock_quantity": 10,
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
    },
)


def seed_products(db: Session) -> None:
    if db.scalar(select(Product.id).limit(1)) is None:
        db.add_all(Product(**product) for product in SEED_PRODUCTS)
        db.commit()


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        expected = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=2**14,
            r=8,
            p=1,
        )
        return hmac.compare_digest(expected, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


def issue_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "email": user.email, "iat": now, "exp": now + timedelta(hours=8)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(
            authorization.removeprefix("Bearer "),
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        user = None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def cart_for_user(db: Session, user: User) -> Cart:
    cart = db.execute(
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .where(Cart.user_id == user.id, Cart.status == "open")
    ).unique().scalar_one_or_none()
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        cart = db.execute(
            select(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .where(Cart.id == cart.id)
        ).unique().scalar_one()
    return cart


def cart_total(cart: Cart) -> Decimal:
    return sum(
        (item.product.price * item.quantity for item in cart.items),
        Decimal("0.00"),
    )


def cart_response(cart: Cart) -> CartResponse:
    return CartResponse(
        id=cart.id,
        status=cart.status,
        items=cart.items,
        total=cart_total(cart),
        created_at=cart.created_at,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_compatibility_columns()
    if SERVICE_ROLE in {"all", "catalog"}:
        with Session(engine) as db:
            seed_products(db)
    yield


app = FastAPI(title=f"E-commerce {SERVICE_ROLE} service", version="0.2.0", lifespan=lifespan)


@app.get("/")
def root():
    return {"service": SERVICE_ROLE, "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": SERVICE_ROLE}


if SERVICE_ROLE in {"all", "identity"}:

    @app.post("/auth/signup", response_model=AuthResponse, status_code=201)
    def signup(data: SignupRequest, db: Session = Depends(get_db)):
        email = data.email.strip().lower()
        if db.scalar(select(User).where(User.email == email)) is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        user = User(email=email, full_name=data.full_name.strip(), password_hash=hash_password(data.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return AuthResponse(access_token=issue_token(user), user=user)

    @app.post("/auth/login", response_model=AuthResponse)
    def login(data: LoginRequest, db: Session = Depends(get_db)):
        user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Email or password is incorrect")
        return AuthResponse(access_token=issue_token(user), user=user)

    @app.get("/auth/me", response_model=UserResponse)
    def me(user: User = Depends(current_user)):
        return user


if SERVICE_ROLE in {"all", "catalog"}:

    @app.get("/products", response_model=list[ProductResponse])
    def get_products(db: Session = Depends(get_db)):
        return db.scalars(select(Product).order_by(Product.id)).all()

    @app.get("/products/{product_id}", response_model=ProductResponse)
    def get_product(product_id: int, db: Session = Depends(get_db)):
        product = db.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    @app.post("/products", response_model=ProductResponse, status_code=201)
    def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
        product = Product(**product_data.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)
        return product


if SERVICE_ROLE in {"all", "commerce"}:

    @app.get("/cart", response_model=CartResponse)
    def get_my_cart(user: User = Depends(current_user), db: Session = Depends(get_db)):
        return cart_response(cart_for_user(db, user))

    @app.post("/cart/items", response_model=CartResponse)
    def add_item(
        data: CartItemRequest,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        cart = cart_for_user(db, user)
        product = db.get(Product, data.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        item = next((entry for entry in cart.items if entry.product_id == product.id), None)
        quantity = data.quantity + item.quantity if item else data.quantity
        if quantity > product.stock_quantity:
            raise HTTPException(status_code=409, detail="Insufficient product stock")
        if item:
            item.quantity = quantity
        else:
            cart.items.append(CartItem(product=product, quantity=quantity))
        db.commit()
        return cart_response(cart_for_user(db, user))

    @app.patch("/cart/items/{product_id}", response_model=CartResponse)
    def update_item(
        product_id: int,
        data: CartItemUpdate,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        cart = cart_for_user(db, user)
        item = next((entry for entry in cart.items if entry.product_id == product_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Cart item not found")
        if data.quantity > item.product.stock_quantity:
            raise HTTPException(status_code=409, detail="Insufficient product stock")
        item.quantity = data.quantity
        db.commit()
        return cart_response(cart_for_user(db, user))

    @app.delete("/cart/items/{product_id}", response_model=CartResponse)
    def remove_item(
        product_id: int,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        cart = cart_for_user(db, user)
        item = next((entry for entry in cart.items if entry.product_id == product_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Cart item not found")
        db.delete(item)
        db.commit()
        return cart_response(cart_for_user(db, user))

    @app.post("/orders", response_model=OrderResponse, status_code=201)
    def create_order(user: User = Depends(current_user), db: Session = Depends(get_db)):
        cart = cart_for_user(db, user)
        if not cart.items:
            raise HTTPException(status_code=409, detail="Cannot order an empty cart")
        for item in cart.items:
            if item.quantity > item.product.stock_quantity:
                raise HTTPException(status_code=409, detail=f"Insufficient stock for {item.product.name}")
        order = Order(user_id=user.id, cart_id=cart.id, total=cart_total(cart))
        order.items = [
            OrderItem(
                product_id=item.product.id,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
            )
            for item in cart.items
        ]
        for item in cart.items:
            item.product.stock_quantity -= item.quantity
        cart.status = "checked_out"
        db.add(order)
        db.commit()
        return db.execute(
            select(Order).options(joinedload(Order.items)).where(Order.id == order.id)
        ).unique().scalar_one()

    @app.get("/orders", response_model=list[OrderResponse])
    def get_orders(user: User = Depends(current_user), db: Session = Depends(get_db)):
        return db.scalars(
            select(Order)
            .options(joinedload(Order.items))
            .where(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
        ).unique().all()
