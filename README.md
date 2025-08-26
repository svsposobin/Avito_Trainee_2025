# Demo PVZ-Service

### Coverage:
> **🔶 - 81%**

### Оглавление:

- [Старт вручную](#title1);
- [Запуск через Docker(Рекомендуемо)](#title2);
- [Как было "Загрумлено" техническое задание?](#title2);
- [Дополнительные утилиты](#title3).

---

### 🔹<a id="title1">Быстрый старт</a>: 🛠

**Для начала работы необходимо:**

1. Установленный Postgres (Для создания БД):

```bash
sudo -u postgres psql
CREATE ROLE pvz_avito WITH LOGIN PASSWORD 'qwerty';
CREATE DATABASE pvz_avito_service OWNER pvz_avito;
GRANT ALL PRIVILEGES ON DATABASE pvz_avito_service TO pvz_avito;
\q
```

Если данной таблицы еще нет, то все должно пройти хорошо

Если скрипт сработал некорректно, авторизуйтесь через sudo еще раз, а потом запустите его еще раз

**Перезапустить Postgres и (Опционально), проверить подключение**

```bash
sudo service postgresql restart  # Перезагрузка Postgres
```

```bash
psql -h 127.0.0.1 -U pvz_avito -d pvz_avito_service  # Проверка подключения
```

2. Установить и запустить проект:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Опционально: Если у вас возникает ошибка интерпретатора, вместо того, чтобы Генерировать новый, переключите выбор на
Select existing**

```bash
pip install -r requirements.txt
python src/main.py
```

---

### 🔹<a id="title2">Запуск в Docker</a>: 🛠

### **Рекомендуемый запуск**

**Чтобы все работало корректно, рекомендуется остановить postgres-сервисы, во избежания конфликтов:**

Возможный конфликт: exposing port TCP 0.0.0.0:5432 -> 127.0.0.1:0: listen tcp 0.0.0.0:5432: bind: address already in
use

Команда для Ubuntu:

```bash
sudo systemctl stop postgresql 
```

Чтобы включить сервисы:

```bash
sudo systemctl start postgresql 
```

----------------------------------------------------------------------------------------------------------------------------
---

**Запустить проект через Docker:**

```bash
docker compose -f deploy/local/docker-compose.yml up -d --build  
```

**Остановить**

```bash
docker compose -f deploy/local/docker-compose.yml down
```

----------------------------------------------------------------------------------------------------------------------------
---
**Проверить контейнеры**

```bash
docker ps -a
```

**Проверить логи контейнеров**

```bash
docker compose -f deploy/local/docker-compose.yml logs app
docker compose -f deploy/local/docker-compose.yml logs db
```

---


### 🔹<a id="title3">Дополнительные утилиты</a>: 🛠

#### Линтер:

```bash
flake8 ./
```

---

#### Типизатор:

```bash
mypy ./
```

---

#### Тесты:

```bash
pytest -v
```

---
