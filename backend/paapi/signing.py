from __future__ import annotations

import datetime as dt
import hashlib
import hmac
from typing import Dict, Tuple


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
    return k_signing


def build_paapi_sigv4_headers(
    *,
    access_key: str,
    secret_key: str,
    region: str,
    host: str,
    amz_target: str,
    payload: bytes,
    now_utc: dt.datetime | None = None,
) -> Dict[str, str]:
    """Build AWS SigV4 headers for Amazon PA-API v5 JSON POST requests.

    Args:
        access_key: AWS access key id
        secret_key: AWS secret access key
        region: AWS region code (e.g., 'us-east-1' for PA-API US)
        host: API host (e.g., 'webservices.amazon.com')
        amz_target: X-Amz-Target value, e.g.,
            'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems'
        payload: raw JSON bytes of the request body
        now_utc: optional dt for deterministic signatures in tests
    """
    method = "POST"
    service = "ProductAdvertisingAPI"
    canonical_uri = "/paapi5/searchitems" if "SearchItems" in amz_target else "/paapi5/getitems"
    canonical_querystring = ""

    content_type = "application/json; charset=UTF-8"
    content_encoding = "amz-1.0"

    now = now_utc or dt.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    payload_hash = _sha256_hex(payload)

    canonical_headers = (
        f"content-encoding:{content_encoding}\n"
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:{amz_target}\n"
    )
    signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"
    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    canonical_request_hash = _sha256_hex(canonical_request.encode("utf-8"))
    string_to_sign = (
        f"{algorithm}\n{amz_date}\n{credential_scope}\n{canonical_request_hash}"
    )

    signing_key = _signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "content-encoding": content_encoding,
        "content-type": content_type,
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-target": amz_target,
        "authorization": authorization_header,
    }

