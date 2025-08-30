import os
from dataclasses import dataclass


@dataclass
class PAAPIConfig:
    access_key: str
    secret_key: str
    partner_tag: str
    region: str = "US"
    host: str = "webservices.amazon.com"
    marketplace: str = "www.amazon.com"


def load_paapi_config() -> PAAPIConfig:
    access_key = os.getenv("PAAPI_ACCESS_KEY", "").strip()
    secret_key = os.getenv("PAAPI_SECRET_KEY", "").strip()
    partner_tag = os.getenv("PAAPI_PARTNER_TAG", "").strip()
    region = os.getenv("PAAPI_REGION", "US").strip() or "US"
    host = os.getenv("PAAPI_HOST", default_host_for_region(region))
    marketplace = os.getenv("PAAPI_MARKETPLACE", default_marketplace_for_region(region))
    return PAAPIConfig(
        access_key=access_key,
        secret_key=secret_key,
        partner_tag=partner_tag,
        region=region,
        host=host,
        marketplace=marketplace,
    )


def default_host_for_region(region: str) -> str:
    r = region.upper()
    return {
        "US": "webservices.amazon.com",
        "UK": "webservices.amazon.co.uk",
        "DE": "webservices.amazon.de",
        "JP": "webservices.amazon.co.jp",
        "FR": "webservices.amazon.fr",
        "CA": "webservices.amazon.ca",
        "IT": "webservices.amazon.it",
        "ES": "webservices.amazon.es",
        "IN": "webservices.amazon.in",
    }.get(r, "webservices.amazon.com")


def default_marketplace_for_region(region: str) -> str:
    r = region.upper()
    return {
        "US": "www.amazon.com",
        "UK": "www.amazon.co.uk",
        "DE": "www.amazon.de",
        "JP": "www.amazon.co.jp",
        "FR": "www.amazon.fr",
        "CA": "www.amazon.ca",
        "IT": "www.amazon.it",
        "ES": "www.amazon.es",
        "IN": "www.amazon.in",
    }.get(r, "www.amazon.com")

