# Аренда вещей (Flask)

Веб-приложение: каталог, корзина, админка для товаров. Бэкенд: **Microsoft SQL Server** и **Flask**.

## Команды подряд (PowerShell)

Из папки, в которой лежит каталог `rental_app`:

```powershell
cd rental_app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DB_NAME = "ProtocolArchive"
$env:DB_SERVER = "localhost\SQLEXPRESS"
python scripts/init_db.py
python app.pyimage.png
```

Подставьте свой экземпляр SQL Server вместо `localhost\SQLEXPRESS`. Сайт: http://127.0.0.1:5000

---

## Что нужно установить

- **Python 3.10+** (лучше 3.11+)
- **Microsoft SQL Server** (Express или полная версия), локально или в сети
- **ODBC Driver 17 for SQL Server** (или новее) — [скачать у Microsoft](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
- По умолчанию используется **вход Windows** (`Trusted_Connection=yes`). Для логина SQL-сервера нужна своя строка подключения в `DB_CONNECTION_STRING` (см. ниже).

## 1. Скопировать проект

```bash
cd rental_app
```

## 2. Виртуальное окружение (рекомендуется)

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Зависимости Python

```bash
pip install -r requirements.txt
```

Пакеты: Flask, pyodbc, deep-translator (опционально, для переводов в интерфейсе).

## 4. Подключение к SQL Server

И приложение, и скрипт `init_db.py` должны смотреть на **один и тот же** сервер, имя базы и способ входа.

### Вариант А — переменные окружения (удобно передавать проект другому человеку)

Задайте их **до** `python scripts/init_db.py` и **до** `python app.py`:

| Переменная | Пример | Назначение |
|------------|--------|------------|
| `DB_NAME` | `ProtocolArchive` | Имя базы данных |
| `DB_SERVER` | `localhost\SQLEXPRESS` | Экземпляр SQL Server (имя ПК и экземпляр) |

**Пример в PowerShell:**

```powershell
$env:DB_NAME = "ProtocolArchive"
$env:DB_SERVER = "localhost\SQLEXPRESS"
```

### Вариант Б — править значения по умолчанию в коде

Если переменные не заданы, в `scripts/init_db.py` используются значения по умолчанию (`DB_SERVER`, `DB_NAME`). Приложение читает `DB_NAME`, `DB_SERVER` и при необходимости полную строку `DB_CONNECTION_STRING` — см. `app.py`.

Чтобы задать всё одной строкой ODBC:

```powershell
$env:DB_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=ProtocolArchive;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;MARS_Connection=no;"
```

## 5. Создать базу и таблицы

Скрипт создаёт базу (если её ещё нет), таблицы и начальный набор брендов для админки:

- `Brands`
- `Products`
- `ProductImages`
- `ProductSizes`
- `CampaignSettings` — тексты страницы «Кампания» (EN/RU)
- `CampaignStories` — истории кампании (заголовок, описание, коллаборация EN/RU)
- `CampaignStoryImages` — фото внутри каждой истории
- `CampaignLooks` — устаревшая таблица; при первом запуске `init_db` данные переносятся в истории, если историй ещё нет

Из папки **`rental_app`**:

```bash
python scripts/init_db.py
```

В консоли появятся сообщения вроде `Created database` / `Database already exists` и `Tables are ready.`

**Важно:** скрипт **не** копирует товары и фото с другого компьютера. После инициализации каталог заполняется через **админку** в приложении либо через восстановление бэкапа SQL (`.bak`), если вы так делаете.

## 6. Запуск приложения

Из **`rental_app`** с активированным venv:

```bash
python app.py
```

Откройте в браузере **http://127.0.0.1:5000**

Альтернатива:

```bash
set FLASK_APP=app.py
flask run --port 5000
```

При `python app.py` режим отладки и порт задаются в `app.py`.

## Чеклист для того, кто разворачивает проект у себя

1. Установить Python, SQL Server, ODBC Driver 17.
2. `python -m venv .venv` и активировать окружение.
3. `pip install -r requirements.txt`
4. Задать `DB_SERVER` / `DB_NAME` (или `DB_CONNECTION_STRING`) под свой SQL Server.
5. `python scripts/init_db.py`
6. `python app.py` → http://127.0.0.1:5000

## Структура проекта (кратко)

- `app.py` — приложение Flask, маршруты
- `scripts/init_db.py` — создание БД и таблиц
- `templates/` — HTML-шаблоны
- `static/` — стили, картинки; загрузки товаров — `static/products/uploads/`; кампания — `static/campaign/uploads/`

---

**Напоминание:** товары и изображения на новый ПК не подтягиваются автоматически — только структура БД и список брендов из скрипта. Полный каталог — через админку или восстановление бэкапа SQL.
