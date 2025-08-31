from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from backend.models import Money, Paging, Product, SearchResponse


class RainforestConfig:
    def __init__(self) -> None:
        self.api_key = os.getenv("RAINFOREST_API_KEY", "").strip()
        # e.g., amazon.com, amazon.co.uk, amazon.de
        self.domain = os.getenv("RAINFOREST_DOMAIN", "amazon.com").strip() or "amazon.com"


class RainforestClient:
    BASE_URL = "https://api.rainforestapi.com/request"

    def __init__(self, cfg: Optional[RainforestConfig] = None, *, timeout: float = 15.0) -> None:
        self.cfg = cfg or RainforestConfig()
        self.timeout = timeout

    def search_items(self, *, keywords: str, page: int = 1) -> SearchResponse:
        params = {
            "api_key": self.cfg.api_key,
            "type": "search",
            "amazon_domain": self.cfg.domain,
            "search_term": keywords,
            "page": page,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(self.BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        products: List[Product] = []
        results = data.get("search_results", [])
        for it in results:
            asin = it.get("asin") or ""
            title = it.get("title") or ""
            brand = it.get("brand")
            price_info = it.get("price") or {}
            amount = price_info.get("value")
            currency = price_info.get("currency")
            price = None
            if amount is not None and currency:
                try:
                    price = Money(amount=str(amount), currency=str(currency))
                except Exception:
                    price = None
            rating = it.get("rating")
            total_reviews = it.get("ratings_total")
            url = it.get("link")
            image = it.get("image")
            images: List[str] = []
            if image:
                images.append(image)

            if asin and title:
                products.append(
                    Product(
                        asin=asin,
                        title=title,
                        brand=brand,
                        categories=[],
                        price=price,
                        list_price=None,
                        savings=None,
                        rating=rating,
                        total_reviews=total_reviews,
                        images=images,  # type: ignore[arg-type]
                        url=url,  # type: ignore[arg-type]
                    )
                )

        total = data.get("search_information", {}).get("total_results")
        paging = Paging(page=page, page_size=len(products), total=total)
        return SearchResponse(products=products, paging=paging)

