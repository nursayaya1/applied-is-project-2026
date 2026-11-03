"""Three related database tables and validated input schemas."""

from sqlmodel import Field, SQLModel


class CategoryCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)


class Category(CategoryCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)


class SupplierCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(default="", max_length=30)


class Supplier(SupplierCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ProductCreate(SQLModel):
    name: str = Field(min_length=1, max_length=120)
    # Store money as integer tiyn to avoid floating-point rounding errors.
    price_tiyn: int = Field(default=0, ge=0)
    quantity: int = Field(default=0, ge=0)
    category_id: int = Field(foreign_key="category.id", gt=0)
    supplier_id: int = Field(foreign_key="supplier.id", gt=0)


class Product(ProductCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
