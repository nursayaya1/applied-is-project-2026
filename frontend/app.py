"""Streamlit UI communicates with FastAPI over HTTP."""

import os
from decimal import Decimal

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Қойма есебі", page_icon="📦", layout="wide")
st.title("📦 Қоймадағы тауарларды есепке алу")
st.caption("Зертханалық жұмыс №1 · FastAPI + SQLModel + Streamlit")


def api(method, path, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}/api/{path}", timeout=10, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        st.error(f"API сұранысы орындалмады. FastAPI серверін тексеріңіз. {error}")
        return None


categories = api("GET", "categories")
suppliers = api("GET", "suppliers")
products = api("GET", "products")
if categories is None or suppliers is None or products is None:
    st.stop()

left, middle, right = st.columns(3)
left.metric("Тауар түрлері", len(products))
middle.metric("Жалпы саны", sum(p["quantity"] for p in products))
total = sum(p["quantity"] * p["price_tiyn"] for p in products)
right.metric("Қойма құны", f"{total / 100:,.2f} ₸")

tab_products, tab_category, tab_supplier = st.tabs(["Тауарлар", "Санаттар", "Жеткізушілер"])
with tab_category:
    with st.form("category"):
        name = st.text_input("Санат атауы", max_chars=100)
        if st.form_submit_button("Санат қосу"):
            if name.strip():
                if api("POST", "categories", json={"name": name.strip()}) is not None:
                    st.rerun()
            else:
                st.warning("Санат атауын енгізіңіз.")
    st.dataframe(categories, width="stretch")

with tab_supplier:
    with st.form("supplier"):
        name = st.text_input("Жеткізуші атауы", max_chars=100)
        phone = st.text_input("Телефон", max_chars=30)
        if st.form_submit_button("Жеткізуші қосу"):
            if name.strip():
                if api("POST", "suppliers", json={"name": name.strip(), "phone": phone.strip()}) is not None:
                    st.rerun()
            else:
                st.warning("Жеткізуші атауын енгізіңіз.")
    st.dataframe(suppliers, width="stretch")

with tab_products:
    if categories and suppliers:
        category_names = {c["id"]: c["name"] for c in categories}
        supplier_names = {s["id"]: s["name"] for s in suppliers}
        with st.form("product"):
            name = st.text_input("Тауар атауы", max_chars=120)
            price = st.number_input("Бағасы, теңге", min_value=0.0, step=1.0, format="%.2f")
            quantity = st.number_input("Саны", min_value=0, step=1)
            category_id = st.selectbox("Санат", list(category_names), format_func=category_names.get)
            supplier_id = st.selectbox("Жеткізуші", list(supplier_names), format_func=supplier_names.get)
            if st.form_submit_button("Тауар қосу"):
                if name.strip():
                    payload = dict(name=name.strip(), price_tiyn=int(Decimal(str(price)).quantize(Decimal("0.01")) * 100),
                                   quantity=quantity, category_id=category_id, supplier_id=supplier_id)
                    if api("POST", "products", json=payload) is not None:
                        st.rerun()
                else:
                    st.warning("Тауар атауын енгізіңіз.")
    else:
        st.info("Алдымен санат пен жеткізуші қосыңыз.")
    if products:
        st.dataframe([{
            "ID": p["id"], "Тауар": p["name"], "Бағасы, ₸": p["price_tiyn"] / 100,
            "Саны": p["quantity"],
            "Санат": next(c["name"] for c in categories if c["id"] == p["category_id"]),
            "Жеткізуші": next(s["name"] for s in suppliers if s["id"] == p["supplier_id"]),
        } for p in products], width="stretch")
    else:
        st.info("Әзірге тауар жоқ.")
