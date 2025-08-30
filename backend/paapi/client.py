from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from backend.config import PAAPIConfig
from backend.models import Money, Paging, Product, SearchResponse
from backend.paapi.signing import build_paapi_sigv4_headers


class PaapiClient:
    def __init__(self, cfg: PAAPIConfig, *, timeout: float = 8.0):
        self.cfg = cfg
        self.timeout = timeout
        # PA-API US uses region us-east-1; other locales vary in docs.
        # Map common region shorthand to SigV4 region for PA-API.
        self.sigv4_region = _sigv4_region_for_locale(cfg.region)
        self.endpoint = f"https://{cfg.host}"

    def _post(self, target: str, uri: str, body: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = build_paapi_sigv4_headers(
            access_key=self.cfg.access_key,
            secret_key=self.cfg.secret_key,
            region=self.sigv4_region,
            host=self.cfg.host,
            amz_target=target,
            payload=payload,
        )
        url = f"{self.endpoint}{uri}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, content=payload)
            resp.raise_for_status()
            return resp.json()

    def search_items(
        self,
        *,
        keywords: str,
        page: int = 1,
        search_index: Optional[str] = None,
        sort_by: Optional[str] = None,
        resources: Optional[List[str]] = None,
    ) -> SearchResponse:
        target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
        uri = "/paapi5/searchitems"
        res = resources or DEFAULT_RESOURCES
        body: Dict[str, Any] = {
            "PartnerTag": self.cfg.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.cfg.marketplace,
            "Keywords": keywords,
            "ItemPage": page,
            "Resources": res,
        }
        if search_index:
            body["SearchIndex"] = search_index
        if sort_by:
            body["SortBy"] = sort_by

        data = self._post(target, uri, body)
        return _transform_search_items(data, page=page)

    def get_items(
        self, *, item_ids: List[str], resources: Optional[List[str]] = None
    ) -> List[Product]:
        target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"
        uri = "/paapi5/getitems"
        res = resources or DEFAULT_RESOURCES
        body: Dict[str, Any] = {
            "PartnerTag": self.cfg.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.cfg.marketplace,
            "ItemIds": item_ids,
            "Resources": res,
        }
        data = self._post(target, uri, body)
        products, _ = _transform_items(data)
        return products


def _sigv4_region_for_locale(locale: str) -> str:
    # Common mapping for PA-API; US uses us-east-1
    mapping = {
        "US": "us-east-1",
        "CA": "us-east-1",
        "BR": "us-east-1",
        "MX": "us-east-1",
        "UK": "eu-west-1",
        "ES": "eu-west-1",
        "FR": "eu-west-1",
        "DE": "eu-west-1",
        "IT": "eu-west-1",
        "SE": "eu-west-1",
        "NL": "eu-west-1",
        "PL": "eu-west-1",
        "TR": "eu-west-1",
        "AE": "eu-west-1",
        "IN": "eu-west-1",
        "JP": "us-west-2",
        "AU": "us-west-2",
        "SG": "us-west-2",
    }
    return mapping.get(locale.upper(), "us-east-1")


DEFAULT_RESOURCES: List[str] = [
    "Images.Primary.Large",
    "ItemInfo.Title",
    "ItemInfo.ByLineInfo",
    "ItemInfo.Classifications",
    "Offers.Listings.Price",
    "Offers.Listings.SavingBasis",
    "Offers.Listings.Savings",
    "Offers.Summaries.LowestPrice",
]


def _transform_search_items(data: Dict[str, Any], *, page: int) -> SearchResponse:
    products, total = _transform_items(data)
    return SearchResponse(products=products, paging=Paging(page=page, page_size=len(products), total=total))


def _transform_items(data: Dict[str, Any]) -> (List[Product], Optional[int]):
    items = (
        data.get("SearchResult", {}).get("Items", [])
        if "SearchResult" in data
        else data.get("ItemsResult", {}).get("Items", [])
    )
    total = data.get("SearchResult", {}).get("TotalResultCount")
    products: List[Product] = []
    for it in items:
        asin = it.get("ASIN") or ""
        title = (
            it.get("ItemInfo", {})
            .get("Title", {})
            .get("DisplayValue")
            or it.get("ItemInfo", {})
            .get("ProductInfo", {})
            .get("Title", {})
            .get("DisplayValue")
            or ""
        )
        brand = (
            it.get("ItemInfo", {})
            .get("ByLineInfo", {})
            .get("Brand", {})
            .get("DisplayValue")
        )
        categories: List[str] = []
        classif = it.get("ItemInfo", {}).get("Classifications", {})
        if isinstance(classif, dict):
            for key in ("Binding", "ProductGroup", "ProductTypeName"):
                val = classif.get(key, {}).get("DisplayValue")
                if val:
                    categories.append(str(val))

        price_obj = (
            it.get("Offers", {})
            .get("Listings", [{}])[0]
            .get("Price")
        )
        list_price_obj = (
            it.get("Offers", {})
            .get("Listings", [{}])[0]
            .get("SavingBasis")
        )
        savings_obj = (
            it.get("Offers", {})
            .get("Listings", [{}])[0]
            .get("Savings")
        )

        price = _money_from_paapi(price_obj)
        list_price = _money_from_paapi(list_price_obj)
        savings = _money_from_paapi(savings_obj)

        rating = it.get("BrowseNodeInfo", {}).get("WebsiteSalesRank", {}).get("SalesRank")
        total_reviews = it.get("CustomerReviews", {}).get("TotalReviewCount")

        images = []
        img = (it.get("Images", {}).get("Primary", {}) or {}).get("Large", {})
        if "URL" in img:
            images.append(img["URL"])

        url = it.get("DetailPageURL")

        if asin and title:
            products.append(
                Product(
                    asin=asin,
                    title=title,
                    brand=brand,
                    categories=categories,
                    price=price,
                    list_price=list_price,
                    savings=savings,
                    rating=rating,
                    total_reviews=total_reviews,
                    images=images,
                    url=url,
                )
            )

    return products, total


def _money_from_paapi(obj: Optional[Dict[str, Any]]) -> Optional[Money]:
    if not obj:
        return None
    amount = obj.get("Amount")
    currency = obj.get("Currency")
    if amount is None or currency is None:
        # Some subfields nest under DisplayAmount and Value; try to normalize
        amount = obj.get("Value") or obj.get("Amount")
        currency = obj.get("Currency")
    if amount is None or currency is None:
        return None
    try:
        return Money(amount=str(amount), currency=str(currency))
    except Exception:
        return None

