# Қоймадағы тауарларды есепке алу

Зертханалық жұмыс №1. Python тіліндегі қойма ақпараттық жүйесінің бастапқы жобасы.
Жүйе тауарларды, олардың санаттарын және жеткізушілерін сақтайды. Санат, жеткізуші және тауар қосуға, тізімдерін көруге, қоймадағы жалпы сан мен құнды есептеуге болады.

## ER-диаграмма

![Қойма дерекқорының ER-диаграммасы](docs/er-diagram.png)

- `Category` → `Product`: бір санатта нөл немесе бірнеше тауар болуы мүмкін.
- `Supplier` → `Product`: бір жеткізуші нөл немесе бірнеше тауар жеткізеді.
- Әр тауарда бір міндетті санат және бір міндетті жеткізуші бар.
- `id` — бастапқы кілт (PK), `category_id` және `supplier_id` — сыртқы кілттер (FK).
- Осы оқу моделінде бір тауарға бір жеткізуші бекітіледі.

Өңделетін сызба: [er-diagram.drawio](docs/er-diagram.drawio). Оны [draw.io](https://app.diagrams.net/) сайтында **File → Open from → Device** арқылы ашыңыз. PNG қайта экспорттау: **File → Export as → PNG**.

## Архитектура

Пайдаланушы → Streamlit интерфейсі → HTTP сұранысы → FastAPI → SQLModel → SQLite.

Streamlit дерекқорға тікелей кірмейді. FastAPI енгізілген мәліметтерді тексеріп, SQLModel арқылы сақтайды. SQLite деректері жобаның түбіріндегі `warehouse.db` файлында болады; файл сервер алғаш іске қосылғанда жасалады.

## Жоба құрылымы

```text
app/
  main.py                  # FastAPI қолданбасы және /health
  api/routes.py            # Санат, жеткізуші, тауар API маршруттары
  models/inventory.py      # Үш кесте және енгізу деректерінің схемалары
  db/session.py            # SQLite қосылымы және сессиялар
frontend/app.py            # Streamlit интерфейсі
docs/
  er-diagram.png           # Тапсыратын ER-диаграмма
  er-diagram.drawio        # Өңделетін түпнұсқа
  GUIDE_KK.md              # Толық түсіндірме және қорғауға дайындық
scripts/create_diagram.py  # Сызбаны қайта жасау құралы (Pillow қажет)
scripts/smoke_check.py     # API мен UI іске қосылуын тексеру
tests/test_api.py          # API тексерістері
.vscode/                  # Python ортасы және ұсынылатын кеңейтімдер
.gitignore                # Git-ке жіберілмейтін файлдар
requirements.txt          # Қолданба кітапханалары
requirements-dev.txt      # Тестілеу кітапханалары
requirements-lock.txt     # Тексерілген орта нұсқалары
README.md                 # Жоба сипаттамасы
```

## Іске қосу

Python 3.12 ұсынылады. Командалар жоба түбіріндегі PowerShell терминалында орындалады.
Осы компьютерде `venv` дайын болса, оны қайта жасаудың қажеті жоқ.

Жаңа компьютерде:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Тексерілген нақты нұсқаларды орнату үшін `requirements.txt` орнына `requirements-lock.txt` пайдалануға болады.

Бірінші терминал — API:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Екінші терминал — интерфейс:

```powershell
.\venv\Scripts\python.exe -m streamlit run frontend/app.py
```

- Интерфейс: http://localhost:8501
- API құжаттамасы: http://127.0.0.1:8000/docs
- Сервер күйі: http://127.0.0.1:8000/health

Ортаға қосылу командасы: `.\venv\Scripts\Activate.ps1`. Жоғарыдағы командалар Python-ды ортадан тікелей шақыратындықтан, активациясыз да жұмыс істейді. Серверді тоқтату: `Ctrl+C`.

## Тексеру мысалы

1. «Санаттар» бөлімінде «Кеңсе тауарлары» қосыңыз.
2. «Жеткізушілер» бөлімінде «Almaty Supply» қосыңыз; мысал үшін телефонды бос қалдыруға болады.
3. «Тауарлар» бөлімінде «Дәптер», бағасы 350 теңге, саны 20 деп енгізіп, осы санат пен жеткізушіні таңдаңыз.
4. Тізімде дәптер, жалпы саны 20, қойма құны 7 000 теңге болуы тиіс.

## API

| Әдіс | Мекенжай | Қызметі |
|---|---|---|
| GET | `/health` | Сервер жұмысын тексеру |
| GET / POST | `/api/categories` | Санаттар тізімі / қосу |
| GET / POST | `/api/suppliers` | Жеткізушілер тізімі / қосу |
| GET / POST | `/api/products` | Тауарлар тізімі / қосу |

POST `/api/products` мысалы (1-нөмірлі санат пен жеткізуші алдын ала жасалуы тиіс):

```json
{"name":"Дәптер","price_tiyn":35000,"quantity":20,"category_id":1,"supplier_id":1}
```

`price_tiyn` ақшаны бүтін санмен сақтайды: 35000 тиын = 350 теңге. Теріс сан/баға — HTTP 422, жоқ санат/жеткізуші — HTTP 404. Қосу сәтті болса — HTTP 201.

## Автоматты тесттер

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\venv\Scripts\python.exe -m pytest -q
```

Тесттер бөлек жедел жад дерекқорында орындалады. Негізгі `warehouse.db` өзгермейді.

API мен интерфейстің іске қосылуын тексеру: `.\venv\Scripts\python.exe scripts/smoke_check.py`. Бұл тексеріс негізгі дерекқорда кестелерді жасайды, бірақ тауар қоспайды; уақытша серверлерін тексерістен кейін тоқтатады.

## Git және AI ортасы

Репозиторий: [nursayaya1/applied-is-project-2026](https://github.com/nursayaya1/applied-is-project-2026).

VS Code үшін Python және GitHub Copilot кеңейтімдері `.vscode/extensions.json` ішінде ұсынылған. Ұсыныс кеңейтімді автоматты орнатпайды; AI кеңейтіміне өз аккаунтыңызбен кіру қажет. Cursor да жарайды.

GitHub-қа жариялау, ИИ промпті, файлдардың мағынасы және қорғау сұрақтары [қазақша нұсқаулықта](docs/GUIDE_KK.md).

Бұл №1 зертхананың бастапқы нұсқасы: қосу және тізімдеу бар; өңдеу, жою, пайдаланушы авторизациясы және тауар қозғалысының тарихы кейінгі кезеңге қалдырылған.

2026-11-03 күнгі тексеріс: 5 API тесті өтті; API іске қосылуы, Swagger, Streamlit бетінің орындалуы және сервердің health жауабы тексерілді. `pip check` кітапхана қайшылығын таппады.

## Ресми құжаттар

- [FastAPI және SQL дерекқорлары](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Streamlit орнату және іске қосу](https://docs.streamlit.io/get-started/installation/command-line)
