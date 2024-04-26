# Инструкция по запуску проекта:

1. `git clone https://github.com/annashutova/battleship_backend` - Склонируйте репозиторий;
2. В папке `battleship_backend/conf` создайте файл `.env`;
```.env
BIND_PORT=8000
BIND_IP=0.0.0.0

DB_URL=postgresql+asyncpg://postgres:postgres@web_db:5432/main_db
JWT_SECRET_SALT=some_salt

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
```

3. Находясь в папке `battleship_backend` поднимите докер:
```shell
docker compose up --build
```

***[Документация API](http://127.0.0.1:8000/swagger)***
