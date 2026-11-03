"""Veterinary clinic UI; all data is accessed through FastAPI."""
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Ветеринарлық клиника", page_icon="🐾", layout="wide")
st.title("🐾 Ветеринарлық клиника")
st.caption("Қабылдауларды есепке алу ақпараттық жүйесі · Зертханалық жұмыс №1")


def api(method, path, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}/api/{path}", timeout=10, **kwargs)
        if not response.ok:
            detail = response.json().get("detail", "Сұраныс орындалмады")
            st.error(f"Қате ({response.status_code}): {detail}")
            return None
        return response.json()
    except requests.RequestException:
        st.error("API-ге қосылу мүмкін болмады. FastAPI серверін бірінші терминалда іске қосыңыз.")
        return None


def submit(path, data):
    if any(isinstance(value, str) and not value.strip() for value in data.values()):
        st.warning("Барлық мәтіндік өрістерді толтырыңыз.")
    elif api("POST", path, json=data) is not None:
        st.rerun()


owners = api("GET", "owners")
pets = api("GET", "pets")
vets = api("GET", "veterinarians")
appointments = api("GET", "appointments")
if any(items is None for items in (owners, pets, vets, appointments)):
    st.stop()

owner_names = {o["id"]: f'{o["name"]} (№{o["id"]})' for o in owners}
pet_names = {p["id"]: f'{p["name"]} — {p["species"]} (№{p["id"]})' for p in pets}
vet_names = {v["id"]: f'{v["name"]} — {v["specialty"]} (№{v["id"]})' for v in vets}
for column, label, items in zip(st.columns(4), ["Иелері", "Жануарлар", "Ветеринарлар", "Қабылдаулар"], [owners, pets, vets, appointments]):
    column.metric(label, len(items))

tab_visits, tab_pets, tab_owners, tab_vets = st.tabs(["Қабылдаулар", "Жануарлар", "Иелері", "Ветеринарлар"])
with tab_owners:
    st.subheader("Жануар иесін тіркеу")
    with st.form("owner"):
        name = st.text_input("Иесінің аты-жөні", max_chars=100)
        phone = st.text_input("Телефон нөмірі", max_chars=30)
        if st.form_submit_button("Иесін қосу"):
            submit("owners", dict(name=name.strip(), phone=phone.strip()))
    st.dataframe([{"ID": o["id"], "Аты-жөні": o["name"], "Телефон": o["phone"]} for o in owners], width="stretch")

with tab_pets:
    st.subheader("Жануарды тіркеу")
    if owners:
        with st.form("pet"):
            name = st.text_input("Жануардың аты", max_chars=100)
            species = st.selectbox("Жануардың түрі", ["Мысық", "Ит", "Құс", "Қоян", "Басқа"])
            age = st.number_input("Толық жасы (жыл)", min_value=0, max_value=100, step=1)
            owner_id = st.selectbox("Иесі", list(owner_names), format_func=owner_names.get)
            if st.form_submit_button("Жануар қосу"):
                submit("pets", dict(name=name.strip(), species=species, age_years=age, owner_id=owner_id))
    else:
        st.info("Алдымен «Иелері» бөлімінде жануардың иесін тіркеңіз.")
    st.dataframe([{"ID": p["id"], "Аты": p["name"], "Түрі": p["species"], "Жасы": p["age_years"], "Иесі": owner_names[p["owner_id"]]} for p in pets], width="stretch")

with tab_vets:
    st.subheader("Ветеринарды тіркеу")
    with st.form("vet"):
        name = st.text_input("Ветеринардың аты-жөні", max_chars=100)
        specialty = st.text_input("Мамандануы", max_chars=100, placeholder="Мысалы: жалпы практика")
        if st.form_submit_button("Ветеринар қосу"):
            submit("veterinarians", dict(name=name.strip(), specialty=specialty.strip()))
    st.dataframe([{"ID": v["id"], "Аты-жөні": v["name"], "Мамандануы": v["specialty"]} for v in vets], width="stretch")

with tab_visits:
    st.subheader("Қабылдауға жазу")
    st.caption("Клиниканың жергілікті уақыты: Asia/Qyzylorda (UTC+5).")
    if pets and vets:
        with st.form("appointment"):
            pet_id = st.selectbox("Жануар", list(pet_names), format_func=pet_names.get)
            veterinarian_id = st.selectbox("Ветеринар", list(vet_names), format_func=vet_names.get)
            day = st.date_input("Қабылдау күні", value=datetime.now(ZoneInfo("Asia/Qyzylorda")).date())
            clock = st.time_input("Қабылдау уақыты", value=time(10, 0), step=1800)
            reason = st.text_area("Келу себебі", max_chars=500, placeholder="Мысалы: жоспарлы тексеру")
            if st.form_submit_button("Қабылдауға жазу"):
                submit("appointments", dict(pet_id=pet_id, veterinarian_id=veterinarian_id,
                       starts_at=datetime.combine(day, clock).isoformat(), reason=reason.strip()))
    else:
        st.info("Қабылдауға жазу үшін алдымен иесін, жануарды және ветеринарды тіркеңіз.")
    if appointments:
        st.dataframe([{"ID": a["id"], "Күні мен уақыты": datetime.fromisoformat(a["starts_at"]).strftime("%d.%m.%Y %H:%M"),
                       "Жануар": pet_names[a["pet_id"]], "Ветеринар": vet_names[a["veterinarian_id"]],
                       "Келу себебі": a["reason"]} for a in appointments], width="stretch")
    else:
        st.info("Әзірге қабылдаулар жоқ.")
