import json
import os
from typing import List

import pandas as pd
import streamlit as st

from backend.config import load_paapi_config
from backend.models import Product

try:
    from backend.paapi.client import PaapiClient
except Exception:  # pragma: no cover - allow UI to render even if deps missing
    PaapiClient = None  # type: ignore


st.set_page_config(page_title="Marketplace Analyzer (Amazon)", layout="wide")
st.title("Marketplace Analyzer — Amazon (MVP)")


def have_paapi_keys() -> bool:
    cfg = load_paapi_config()
    return bool(cfg.access_key and cfg.secret_key and cfg.partner_tag)


def to_frame(products: List[Product]) -> pd.DataFrame:
    def money_fmt(m):
        if not m:
            return None
        return f"{m.amount} {m.currency}"

    rows = []
    for p in products:
        rows.append(
            {
                "ASIN": p.asin,
                "Title": p.title,
                "Brand": p.brand,
                "Price": money_fmt(p.price),
                "List Price": money_fmt(p.list_price),
                "Savings": money_fmt(p.savings),
                "Rating": p.rating,
                "Reviews": p.total_reviews,
                "URL": str(p.url) if p.url else None,
            }
        )
    return pd.DataFrame(rows)


with st.sidebar:
    st.header("Search")
    keywords = st.text_input("Keywords", value="mechanical keyboard")
    page = st.number_input("Page", min_value=1, value=1, step=1)
    submitted = st.button("Search")
    st.markdown("—")
    if not have_paapi_keys():
        st.info("No PA-API keys detected. Running in sample mode.")


def run_search():
    if have_paapi_keys() and PaapiClient is not None:
        cfg = load_paapi_config()
        client = PaapiClient(cfg)
        resp = client.search_items(keywords=keywords, page=page)
        return resp.products
    # sample mode
    sample_path = os.path.join(os.path.dirname(__file__), "../samples/search_sample.json")
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    from backend.paapi.client import _transform_search_items  # reuse transformer

    sr = _transform_search_items(data, page=1)
    return sr.products


if submitted:
    with st.spinner("Searching..."):
        products = run_search()
    if not products:
        st.warning("No results.")
    else:
        df = to_frame(products)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Simple price distribution
        price_vals = [float(p.price.amount) for p in products if p.price]
        if price_vals:
            st.subheader("Price distribution")
            st.bar_chart(price_vals)

        # Detail view for the first product
        first = products[0]
        with st.expander("First result details"):
            cols = st.columns([1, 2])
            with cols[0]:
                if first.images:
                    st.image(first.images[0])
            with cols[1]:
                st.write(f"ASIN: {first.asin}")
                st.write(f"Title: {first.title}")
                st.write(f"Brand: {first.brand}")
                st.write(f"Price: {first.price.amount} {first.price.currency}" if first.price else "Price: -")
                if first.url:
                    st.markdown(f"[Open on Amazon]({first.url})")

