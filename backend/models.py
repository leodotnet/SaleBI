from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class Money(BaseModel):
    amount: Decimal
    currency: str


class Product(BaseModel):
    asin: str
    title: str
    brand: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    price: Optional[Money] = None
    list_price: Optional[Money] = None
    savings: Optional[Money] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    images: List[HttpUrl] = Field(default_factory=list)
    url: Optional[HttpUrl] = None


class Paging(BaseModel):
    page: int = 1
    page_size: int = 24
    total: Optional[int] = None


class SearchResponse(BaseModel):
    products: List[Product]
    paging: Paging

