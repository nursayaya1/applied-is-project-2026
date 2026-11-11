"""Veterinary clinic UI; all data is accessed through FastAPI."""
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo
import requests
import streamlit as st

API_URL = os.getenv("BACKEND_URL", os.getenv("API_URL", "http://127.0.0.1:8000")).rstrip("/")
st.set_page_config(page_title="Ветеринарлық клиника", page_icon="🐾", layout="wide")
st.title("🐾 Ветеринарлық клиника")
st.caption("Қабылдауларды есепке алу")


def api(method, path, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}/api/{path}", timeout=10, **kwargs)
        if not response.ok:
            if response.status_code == 409:
                message = "Бұл уақыт бос емес немесе жазба басқа мәліметтермен байланысты."
            elif response.status_code == 404:
                message = "Жазба табылмады. Тізімді жаңартыңыз."
            elif response.status_code == 422:
                message = "Енгізілген мәліметтерді тексеріңіз: міндетті өрістер бос болмауы тиіс."
            else:
                message = "Сұранысты орындау мүмкін болмады. Кейінірек қайталаңыз."
            st.error(message)
            return None
        if response.status_code == 204:
            return {}
        return response.json()
    except requests.RequestException:
        st.error("Қызметке қосылу мүмкін болмады. Серверді іске қосып, бетті жаңартыңыз.")
        return None
    except ValueError:
        st.error("Серверден жарамсыз жауап келді. Кейінірек қайталаңыз.")
        return None


def submit(path, data):
    if any(isinstance(value, str) and not value.strip() for value in data.values()):
        st.warning("Барлық мәтіндік өрістерді толтырыңыз.")
    elif api("POST", path, json=data) is not None:
        st.session_state["notice"] = "Жазба сәтті қосылды."
        st.rerun()


def filtered(path, original, **params):
    params = {key: value for key, value in params.items() if value not in (None, "")}
    if not params:
        return original
    result = api("GET", path, params=params)
    return result if result is not None else []


def delete_panel(path, rows, labels):
    if not rows:
        return
    with st.expander("Жазбаны жою"):
        selected = st.selectbox("Жойылатын жазба", [row["id"] for row in rows],
                                format_func=lambda key: labels.get(key, str(key)), key=f"delete_select_{path}")
        st.caption("Жою қайтарылмайды. Байланысты жазбалары бар нысанды алдымен босату керек.")
        confirmed = st.checkbox("Осы жазбаны жоюды растаймын", key=f"confirm_{path}_{selected}")
        if st.button("Жою", key=f"delete_{path}", disabled=not confirmed):
            if api("DELETE", f"{path}/{selected}") is not None:
                st.session_state["notice"] = "Жазба жойылды."
                st.rerun()


with st.sidebar:
    st.header("Клиника")
    st.write("Жануарларды тіркеу және қабылдауларды басқару")
    st.caption("Жұмыс реті: иесі → жануар → ветеринар → қабылдау.")
    st.button("Тізімді жаңарту", key="refresh")

if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

collections = {}
for path in ("owners", "pets", "veterinarians", "appointments"):
    collections[path] = api("GET", path)
    if collections[path] is None:
        st.stop()
owners, pets, vets, appointments = (collections[path] for path in ("owners", "pets", "veterinarians", "appointments"))


owner_names = {o["id"]: f'{o["name"]} (№{o["id"]})' for o in owners}
pet_names = {p["id"]: f'{p["name"]} — {p["species"]} (№{p["id"]})' for p in pets}
vet_names = {v["id"]: f'{v["name"]} — {v["specialty"]} (№{v["id"]})' for v in vets}
for column, label, items in zip(st.columns(4), ["Иелері", "Жануарлар", "Ветеринарлар", "Қабылдаулар"], [owners, pets, vets, appointments]):
    column.metric(label, len(items))

tab_visits, tab_pets, tab_owners, tab_vets = st.tabs(["Қабылдаулар", "Жануарлар", "Иелері", "Ветеринарлар"])
with tab_owners:
    owner_search = st.text_input("Иесінің аты бойынша іздеу", key="owner_search")
    shown_owners = filtered("owners", owners, search=owner_search.strip())
    st.subheader("Жануар иесін тіркеу")
    with st.form("owner"):
        name = st.text_input("Иесінің аты-жөні", max_chars=100)
        phone = st.text_input("Телефон нөмірі", max_chars=30)
        if st.form_submit_button("Иесін қосу"):
            submit("owners", dict(name=name.strip(), phone=phone.strip()))
    st.dataframe([{"ID": o["id"], "Аты-жөні": o["name"], "Телефон": o["phone"]} for o in shown_owners], width="stretch")
    delete_panel("owners", shown_owners, owner_names)

with tab_pets:
    pet_search = st.text_input("Жануар аты бойынша іздеу", key="pet_search")
    species_filter = st.selectbox("Түрі бойынша сүзу", ["Барлығы", "Мысық", "Ит", "Құс", "Қоян", "Басқа"], key="species_filter")
    ages = st.slider("Жас аралығы", 0, 100, (0, 100), key="age_filter")
    shown_pets = filtered("pets", pets, search=pet_search.strip(),
                          species=None if species_filter == "Барлығы" else species_filter,
                          min_age=ages[0], max_age=ages[1])
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
    st.dataframe([{"ID": p["id"], "Аты": p["name"], "Түрі": p["species"], "Жасы": p["age_years"], "Иесі": owner_names.get(p["owner_id"], "Иесі табылмады")} for p in shown_pets], width="stretch")
    delete_panel("pets", shown_pets, pet_names)

with tab_vets:
    vet_search = st.text_input("Ветеринар аты бойынша іздеу", key="vet_search")
    shown_vets = filtered("veterinarians", vets, search=vet_search.strip())
    st.subheader("Ветеринарды тіркеу")
    with st.form("vet"):
        name = st.text_input("Ветеринардың аты-жөні", max_chars=100)
        specialty = st.text_input("Мамандануы", max_chars=100, placeholder="Мысалы: жалпы практика")
        if st.form_submit_button("Ветеринар қосу"):
            submit("veterinarians", dict(name=name.strip(), specialty=specialty.strip()))
    st.dataframe([{"ID": v["id"], "Аты-жөні": v["name"], "Мамандануы": v["specialty"]} for v in shown_vets], width="stretch")
    delete_panel("veterinarians", shown_vets, vet_names)

with tab_visits:
    reason_search = st.text_input("Келу себебі бойынша іздеу", key="reason_search")
    shown_visits = filtered("appointments", appointments, search=reason_search.strip())
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
    if shown_visits:
        st.dataframe([{"ID": a["id"], "Күні мен уақыты": datetime.fromisoformat(a["starts_at"]).strftime("%d.%m.%Y %H:%M"),
                       "Жануар": pet_names.get(a["pet_id"], "Жануар табылмады"), "Ветеринар": vet_names.get(a["veterinarian_id"], "Ветеринар табылмады"),
                       "Келу себебі": a["reason"]} for a in shown_visits], width="stretch")
        delete_panel("appointments", shown_visits, {a["id"]: f"№{a['id']} · {pet_names.get(a['pet_id'], 'Жануар')} · {a['starts_at']}" for a in shown_visits})
    else:
        st.info("Бұл іздеу бойынша қабылдаулар жоқ.")
