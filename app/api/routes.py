from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.inventory import (
    Category, CategoryCreate, Product, ProductCreate, Supplier, SupplierCreate,
)

router = APIRouter(prefix="/api")
DBSession = Annotated[Session, Depends(get_session)]


@router.get("/categories", response_model=list[Category])
def list_categories(session: DBSession):
    return session.exec(select(Category).order_by(Category.id)).all()


@router.post("/categories", response_model=Category, status_code=201)
def create_category(data: CategoryCreate, session: DBSession):
    category = Category.model_validate(data)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/suppliers", response_model=list[Supplier])
def list_suppliers(session: DBSession):
    return session.exec(select(Supplier).order_by(Supplier.id)).all()


@router.post("/suppliers", response_model=Supplier, status_code=201)
def create_supplier(data: SupplierCreate, session: DBSession):
    supplier = Supplier.model_validate(data)
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    return supplier


@router.get("/products", response_model=list[Product])
def list_products(session: DBSession):
    return session.exec(select(Product).order_by(Product.id)).all()


@router.post("/products", response_model=Product, status_code=201)
def create_product(data: ProductCreate, session: DBSession):
    if session.get(Category, data.category_id) is None:
        raise HTTPException(404, "Category not found")
    if session.get(Supplier, data.supplier_id) is None:
        raise HTTPException(404, "Supplier not found")
    product = Product.model_validate(data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product
