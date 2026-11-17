from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProductResponse(BaseModel):
    id: int
    name: str
    brand: str
    description: str
    price: Decimal
    category: str
    image_url: str | None
    stock_quantity: int

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    brand: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    image_url: str | None = None
    stock_quantity: int = Field(ge=0)


class CartItemRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    product: ProductResponse
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: str
    status: str
    items: list[CartItemResponse]
    total: Decimal
    created_at: datetime


class OrderRequest(BaseModel):
    cart_id: str = Field(min_length=36, max_length=36)


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: str
    cart_id: str
    status: str
    total: Decimal
    items: list[OrderItemResponse]
    created_at: datetime
