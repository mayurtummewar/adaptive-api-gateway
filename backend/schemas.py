from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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
    description: str
    price: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    image_url: str | None = None
    stock_quantity: int = Field(ge=0)