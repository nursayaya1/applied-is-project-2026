# Зертханалық жұмыс 6 — Docker және Compose

Екі компонент бөлек контейнерге дайындалған: `Dockerfile` — FastAPI, `Dockerfile.frontend` — Streamlit. Базалық орта Python 3.12 slim (тапсырмадағы Python 3.11+ талабына сай).

## Осы компьютердегі тексеру күйі — 2026-11-11

Docker файлдары дайын, бірақ контейнерлерді құрастыру және іске қосу осы компьютерде **тексерілген жоқ**. Docker Desktop орнатылмаған; ресми орнатқышты жүктеу уақыт шегінен асты. WSL орнатқышы 0x80073d28 қатесін қайтарды: әкімші құқығы қажет. Компьютер пайдаланушысында әкімші құқығы жоқ.

Жергілікті Python режимінде FastAPI, Swagger және Streamlit іске қосылып тексерілді; 35 автоматты тест өтті. Бұл Docker тексеруін алмастырмайды. №6-ны толық көрсету және №7-нің контейнерлік көрсету талабын орындау үшін Docker орнатылған зертхана компьютері немесе әкімші орнатқан Docker Desktop қажет. Сол компьютерде төмендегі командаларды орындаңыз. Қайта жүктеу не әкімші орнатуы бұл жобаның Python режиміне қажет емес.

## Құрылымы

Алдымен requirements көшіріліп, кітапханалар орнатылады; одан кейін код көшіріледі. Код қана өзгерсе, тәуелділіктер қабатын қайта жүктеудің қажеті жоқ. Әр компонент тек өз кітапханаларын орнатады.

`docker-compose.yml` ішінде backend және frontend бар. Frontend `BACKEND_URL=http://backend:8000` арқылы серверге қосылады. Екі сервис clinic bridge желісінде; Compose-тың DNS қызметі `backend` атын контейнер IP-іне сәйкестендіреді. Контейнер ішіндегі localhost сол контейнердің өзін білдіреді.

Frontend backend healthcheck сәтті болғаннан кейін іске қосылады. Host порттары тек 127.0.0.1-ге жарияланған. SQLite `/data/vet_clinic.db` ішінде, `clinic_data` volume-ында сақталады.

Қазіргі Compose Specification қолданылады: ескірген `version: '3.8'` өрісі қажет емес. Команда — `docker compose`, ескі нұсқада `docker-compose` деп жазылатын.

## Windows-та дайындау

Docker Desktop және WSL 2 керек. Егер орнатқыш қайта жүктеуді сұраса, жұмысыңызды сақтап, компьютерді өзіңіз қайта қосыңыз. Docker Desktop-ты ашып, бастапқы келісімдер мен баптауды аяқтаңыз. Terminal ішінде `docker version` командасында Client және Server екеуі де болуы тиіс.

## Іске қосу

Бұрынғы uvicorn және Streamlit терминалдарын Ctrl+C арқылы тоқтатыңыз. Жоба түбірінде:

```powershell
docker compose config
docker compose up --build -d
docker compose ps
docker compose exec backend python seed.py
```

Интерфейс: http://localhost:8501. Swagger: http://localhost:8000/docs.

Контейнердің базасы жергілікті Python режиміндегі базадан бөлек. Seed қажет бастапқы жазбаларды контейнердің volume-ына қосады. Host-тағы деректер автоматты көшірілмейді және өшірілмейді.

## Тұрақтылықты тексеру

1. Беттен сынақ иесін қосыңыз.
2. `docker compose down` орындаңыз.
3. `docker compose up -d` орындаңыз.
4. Жаңа жазба сақталуы керек.

`docker compose down` volume-ды сақтайды. `down -v` деректер volume-ын жояды — зертхананы қайта іске қосу үшін бұл параметр қажет емес.

Логтар: `docker compose logs --tail 100`. Дерекқор: `docker compose exec backend python -m scripts.inspect_db`.

## Қорғау жауаптары

Контейнер host ядросын қолданатын оқшауланған процесс; виртуалды машина жеке guest операциялық жүйемен жұмыс істейді. Windows-та Linux контейнерлері WSL 2 ортасын пайдаланады.

- WORKDIR — жұмыс папкасы.
- COPY — файлдарды image-ке көшіреді.
- RUN — image құрастырылғанда орындалады.
- CMD — контейнер басталғанда орындалады.
- EXPOSE — қолданылатын портты сипаттайды; host-қа порт жариялау Compose ports арқылы жасалады.
- .dockerignore — venv, жергілікті база, кэш және құпия файлдардың build context-ке түсуін болдырмайды.

ИИ промпті: «FastAPI және Streamlit үшін екі Dockerfile және Compose жаса. BACKEND_URL сервис атымен берілсін; healthcheck, depends_on және SQLite volume болсын».

Ресми құжаттар: [іске қосу реті](https://docs.docker.com/compose/how-tos/startup-order/), [Compose бастапқы нұсқаулығы](https://docs.docker.com/compose/gettingstarted/).
