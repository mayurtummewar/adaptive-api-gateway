from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Product
from schemas import ProductResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="E-commerce Backend",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "service": "ecommerce-backend",
        "message": "E-commerce API is running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get(
    "/products",
    response_model=list[ProductResponse],
)
def get_products(db: Session = Depends(get_db)):
    products = db.scalars(
        select(Product).order_by(Product.id)
    ).all()

    return products


@app.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product