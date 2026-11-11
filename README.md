# Информационная система: Ветеринарлық клиника

**Курс:** Прикладное программное обеспечение информационных систем (2026 г.)

**Автор:** ИС 24 А1 тобының студенті — Жұматай Нұрсая

## 1. Описание предметной области

Жүйе ветеринарлық клиникадағы қабылдауларды есепке алуға арналған. Оны клиника әкімшісі жануар иелерін, жануарларды және ветеринарларды тіркеуге қолданады. Әкімші жануарды нақты дәрігерге күнін, уақытын және келу себебін көрсетіп жазады. Жүйе мәліметтерді іздеуді, сүзуді, қосуды, өзгертуді және жоюды автоматтандырады. Бір дәрігерді немесе жануарды дәл бір уақытқа қайталап жазуға жол бермейді.

## 2. Архитектура данных (ER-диаграмма)

![Дерекқор схемасы](docs/er-diagram.png)

| Кесте | Мазмұны және байланысы |
|---|---|
| Owner | Иесінің аты мен телефоны. Owner → Pet: бірден көпке. |
| Pet | Жануар аты, түрі, жасы, owner_id. Pet → Appointment: бірден көпке. |
| Veterinarian | Ветеринар аты және мамандануы. Veterinarian → Appointment: бірден көпке. |
| Appointment | pet_id, veterinarian_id, басталу уақыты, келу себебі. |

Pet ↔ Veterinarian көптен көпке байланысы Appointment арқылы жасалған; ORM-де оны тек оқуға арналған veterinarians/patients байланыстары көрсетеді. id — PK; owner_id, pet_id, veterinarian_id — FK.

[Өңделетін draw.io схемасы](docs/er-diagram.drawio).

## 3. Технологический стек

- **Backend:** Python 3.12 (3.11+), FastAPI, Uvicorn.
- **Database / ORM:** SQLite, SQLModel / SQLAlchemy.
- **Frontend UI:** Streamlit, Requests.
- **DevOps / Инфраструктура:** Docker, Docker Compose, Git / GitHub.
- **Тесттер:** pytest, FastAPI TestClient / httpx, Streamlit AppTest.
- **AI-tools:** Codex — кодты дайындау, тексеру және түсіндіруге көмек.

Архитектура: браузер → Streamlit → HTTP API → FastAPI → SQLModel → SQLite. Интерфейс базаға тікелей қосылмайды.

```text
app/
  main.py                  # FastAPI, lifespan, /health
  api/routes.py            # GET, POST, PATCH, DELETE және сүзу
  models/clinic.py         # ORM, Relationship, Create/Update схемалары
  db/session.py            # engine, init_db, get_session
  db/seed.py               # Қайталанбайтын бастапқы деректер
frontend/app.py            # Streamlit формалары, іздеу, жою
tests/                    # API, база және интерфейс тесттері
scripts/                  # Базаны тексеру және іске қосу сынағы
docs/                     # ER-схема және зертхана нұсқаулықтары
seed.py                   # Бастапқы деректерді қосу
Dockerfile                # Backend image
Dockerfile.frontend       # Frontend image
docker-compose.yml        # Сервистер, желі, healthcheck, volume
.dockerignore             # Build context ерекшеліктері
requirements.txt          # Жергілікті орта және тест кітапханалары
requirements-backend.txt  # Backend контейнерінің кітапханалары
requirements-frontend.txt # Frontend контейнерінің кітапханалары
```

Әдістемедегі database/, routers/, app/frontend/ міндеттері тиісінше app/db/ + app/models/, app/api/, frontend/ модульдеріне бөлінген.

## 4. Инструкция по локальному развертыванию

### Docker арқылы

Docker Desktop орнатылып, Linux engine іске қосылуы керек. Windows-та WSL 2 қажет. `docker version` Client және Server нұсқаларын көрсетуі тиіс. Бұл режимде host компьютерге Python немесе SQLite бөлек орнату қажет емес.

```powershell
git clone https://github.com/nursayaya1/applied-is-project-2026.git
cd applied-is-project-2026
docker compose config
docker compose up --build -d
docker compose ps
docker compose exec backend python seed.py
```

- Интерфейс: [localhost:8501](http://localhost:8501).
- Swagger: [localhost:8000/docs](http://localhost:8000/docs).
- Күйі: [localhost:8000/health](http://localhost:8000/health).

Егер 8000/8501 порттарында жергілікті серверлер жұмыс істесе, олардың терминалдарында Ctrl+C басыңыз. Frontend BACKEND_URL=http://backend:8000 арқылы backend-ке қосылады және backend дайын болғанша күтеді.

SQLite /data/vet_clinic.db файлы clinic_data volume-ында сақталады. `docker compose down` және қайта `docker compose up -d` орындағанда деректер қалады. `down -v` қолданбаңыз: ол volume деректерін жояды. Жергілікті Python базасы мен контейнер базасы бөлек.

### Python арқылы (Docker қажет емес)

Windows PowerShell, жоба папкасында:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe seed.py
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Бірінші терминалды ашық қалдырып, екінші терминалда:

```powershell
.\venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Mac/Linux-та venv/bin/python қолданыңыз. Seed бос базаға 3 ие, 3 жануар, 3 ветеринар, 4 қабылдау қосады; қайта орындағанда көбейтпейді. База, виртуалды орта және құпия файлдар Git-ке жіберілмейді.

## 5. Запуск тестов

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m scripts.smoke_check
```

Виртуалды орта белсенді болса, `pytest` жеткілікті. Тесттер оқшауланған SQLite базаларын қолданады және жұмыс жазбаларын өзгертпейді. API тесттері GET/POST/PATCH/DELETE, 404/409/422, сыртқы кілттер, уақыт қайшылығы, іздеу мен сүзуді қамтиды. AppTest интерфейстегі қосу, іздеу, жою және API қателерін тексереді. Smoke check уақытша серверлерді 18001/18501 порттарында іске қосып, тексеруден кейін тоқтатады.

2026-11-11: **35 passed**. TestClient тәуелділігінен бір deprecation ескертуі бар; тесттер сәтті аяқталады. Docker тексеруінің күйі [№6 нұсқаулығында](docs/LAB_06_KK.md) көрсетіледі.

## 6. Зертханалар және қорғау

| Жұмыс | Нұсқаулық |
|---|---|
| №1 | [Орта, Git, ER және іске қосу](docs/GUIDE_KK.md) |
| №2 | [ORM, байланыстар, seed](docs/LAB_02_KK.md) |
| №3 | [GET, POST, Swagger](docs/LAB_03_KK.md) |
| №4 | [PATCH, DELETE, сүзу](docs/LAB_04_KK.md) |
| №5 | [Streamlit интерфейсі](docs/LAB_05_KK.md) |
| №6 | [Docker және Compose](docs/LAB_06_KK.md) |
| №7 | [Тесттер, аудит және қорғау](docs/LAB_07_KK.md) |

Интерфейсте төрт бөлім бар: иелер, жануарлар, ветеринарлар, қабылдаулар. Іздеу үшін мәтін енгізіп Enter басыңыз; қосу үшін форманы толтырыңыз; жою үшін «Жазбаны жою» бөлімін ашып, жазбаны таңдап, растау белгісін қойыңыз. PATCH арқылы өңдеу Swagger-де орындалады.

Шектеулер: авторизация мен рөлдер жоқ; жоба жергілікті оқу/демонстрацияға арналған. Қабылдау ұзақтығы есептелмейді, тек басталу уақытының дәл қайталануы тексеріледі. Коммиттер нақты жасалған уақытын көрсетеді; жеті аптаға жасанды тарих жасалмайды.
