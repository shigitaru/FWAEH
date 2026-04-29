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
# опционально: только вшитые 5 товаров + кампания из seed_defaults.py и папок static/*
# python scripts/seed_demo_content.py
python app.py
```

Подставьте свой экземпляр SQL Server вместо `localhost\SQLEXPRESS`. Сайт: http://127.0.0.1:5000. Перед первым запуском положите фото в `static/products/` и `static/campaign/` (см. раздел 5), если нужны локальные кадры.

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
| `SEED_FULL_DEMO` | `1` | (Только при **первом** `init_db`.) Залить **весь** список `DEMO_PRODUCTS` из `seed_defaults.py`. Без неё в БД попадают только **5 вшитых** артикулов (`DEMO_WIRED_PRODUCT_SERIALS`). |

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

Скрипт создаёт базу (если её ещё нет), таблицы, начальный набор брендов и **демо-данные из `seed_defaults.py`**:

- `Brands`
- `Products`, `ProductImages`, `ProductSizes`
- `CampaignSettings` — тексты страницы «Кампания» (EN/RU)
- `CampaignStories` — истории кампании (заголовок, описание, коллаборация EN/RU)
- `CampaignStoryImages` — фото внутри каждой истории
- `CampaignLooks` — кадры для обложек; при сиде заполняется вместе с историями

Из папки **`rental_app`**:

```bash
python scripts/init_db.py
```

В консоли появятся сообщения вроде `Created database` / `Database already exists` и `Tables are ready.`

При первом создании таблиц вызывается **`apply_demo_seed`**: в каталог попадает **полный** список `DEMO_PRODUCTS` из `seed_defaults.py`, затем синхронизируются галереи товаров с локальными файлами в `static/products/` (см. ниже), кампания — из `static/campaign/` или запасной набор URL.

Переменная окружения **`SEED_RESET_DEMO=1`** (перед `init_db`) заставит при создании таблиц **сначала очистить** товары и кампанию и залить их заново из `seed_defaults.py` (редко нужно при первом запуске).

### Демо-каталог и кампания без полного `init_db`

Чтобы **сбросить** текущие товары и истории кампании и залить **только вшитые** позиции (дипломный набор) + кампанию по правилам из `seed_defaults.py`:

```bash
python scripts/seed_demo_content.py
```

- **Товары:** пять артикулов — `RO-0001` (Kiss Heels), `RS-0001` (Raf bomber), `YZY-9999` (grillz), `BAL-0001` (джинсы), `BC-0001` (сумка Getaria, кутюр). Список задаётся в `seed_defaults.py` (`DEMO_WIRED_PRODUCT_SERIALS`, функция `wired_demo_products()`).
- **Кампания:** если в папке `static/campaign/` есть файлы `campaign-1.jpg`, `campaign-02.png` и т.п. (сортировка по номеру), создаётся **одна** история со **всеми** этими кадрами в галерее; иначе подставляется запасной набор внешних URL из того же файла.

Пользователей (`AppUsers`) скрипт не трогает.

### Локальные фото товаров (`static/products/`)

Имена файлов (расширения: `png`, `jpg`, `jpeg`, `webp`):

| Артикул / товар | Шаблон имён |
|-----------------|-------------|
| `RO-0001` | `kiss-heels-1`, `kiss-heels-2`, … |
| `RS-0001` | `raf-bomber-1`, … |
| `YZY-9999` | `yzy-1`, … |
| `BAL-0001` | `balenciaga-1`, … |
| `BC-0001` | `couturebag.jpg` или `couturebag-1.png`, … |

Если локальных файлов нет, для части позиций используются URL из `seed_defaults.py` (fallback).

### Локальные фото кампании (`static/campaign/`)

Шаблон: **`campaign-<номер>.<расширение>`** (например `campaign-01.jpg`). Все найденные кадры объединяются в **одну** историю на странице кампании.

На **главной** и странице **`/collection`** для витрины **ready-to-wear** доступна панель **фильтров**: текстовый поиск (название, артикул, бренд, материал), бренд, минимальное состояние, сортировка по цене, максимальная цена за день. Страница **Поиск** в шапке ищет по всему каталогу простым совпадению в названии, артикуле и бренде.

## 6. Запуск приложения

Из **`rental_app`** с активированным venv:

```bash
python app.py
```

Откройте в браузере **http://127.0.0.1:5000**

Альтернатива (из **`rental_app`**, venv активен):

**PowerShell**

```powershell
$env:FLASK_APP = "app.py"
flask run --port 5000
```

**CMD**

```bat
set FLASK_APP=app.py
flask run --port 5000
```

При `python app.py` режим отладки и порт задаются в `app.py`.

## Чеклист для того, кто разворачивает проект у себя

1. Установить Python, SQL Server, ODBC Driver 17.
2. `python -m venv .venv` и активировать окружение.
3. `pip install -r requirements.txt`
4. Задать `DB_SERVER` / `DB_NAME` (или `DB_CONNECTION_STRING`) под свой SQL Server.
5. Положить свои фото в `static/products/` и `static/campaign/` (по шаблонам выше), если нужны локальные кадры.
6. `python scripts/init_db.py` — в каталог по умолчанию попадают **только 5 вшитых** товаров; расширенный демо-набор (Margiela, Vetements, …) — задайте **`SEED_FULL_DEMO=1`** **до** этого шага или выполните позже `python scripts/seed_demo_content.py` после сброса (скрипт с `reset=True` снова оставляет только вшитые пять).
7. Если база уже создана со «старым» полным сидом и на главной лишние позиции: `python scripts/seed_demo_content.py` — витрина станет как в `seed_defaults` для вшитых артикулов.
8. `python app.py` → http://127.0.0.1:5000

## Структура проекта (кратко)

- `app.py` — точка входа Flask: создание `app`, `before_request`, регистрация роутов и `context_processor`
- `core/` — общие модули приложения (импорт: `from core.<модуль> import ...`):
  - `core/i18n.py` — словари переводов и функции `t` / `tc` / `tv`
  - `core/constants.py` — статусы заказов, fallback-каталог, бренды, категории вещей, `normalize_item_category_slug`
  - `core/session_cart.py` — корзина, wishlist, текущий пользователь из сессии
  - `core/rental_wrappers.py` — обёртки над `rental_service` для проверки доступности
  - `core/rental_orders.py` — схема заказов, чекаут, история и админ-список заказов
  - `core/account_service.py` — вставка/поиск пользователя для auth
  - `core/catalog.py` — выборка товаров из БД с fallback на `PRODUCTS`
  - `core/listing.py` — контекст листинга коллекции (фильтры, `url_for`)
  - `core/media_uploads.py` — загрузка изображений товаров и кампании, правки галереи в админке
  - `core/campaign_service.py` — публичные данные кампании и админские запросы к stories/settings
  - `core/config.py` — конфигурация (DB, пути загрузок, разрешённые расширения)
  - `core/db.py` — подключение к SQL Server (`get_db_connection`)
- `routes/` — маршруты приложения:
  - `routes/public.py` — публичные страницы, корзина, wishlist, checkout, campaign/about
  - `routes/api.py` — API-эндпоинты (`/api/*`)
  - `routes/auth.py` — аккаунт, login/register/logout, members
  - `routes/admin.py` — операции админки (товары, бренды, заказы, campaign stories)
- `services/` — бизнес-логика:
  - `services/rental_service.py` — период аренды, парсинг дат, проверка доступности
- `repositories/` — слой доступа к данным:
  - `repositories/user_repository.py` — операции с пользователями
- `seed_defaults.py` — единый источник демо-товаров, текстов кампании, правил локальных галерей и fallback-URL
- `scripts/init_db.py` — создание БД, таблиц, первичный сид через `apply_demo_seed`
- `scripts/seed_demo_content.py` — сброс товаров и кампании + заливка вшитого набора товаров и кампании
- `templates/` — HTML-шаблоны
- `static/` — `style.css`, сплэш `splash.jpg`, знак в шапке `header-logo-mark.png`, шрифт бренда `fonts/SignThat-Regular.ttf`
- `static/products/` — демо-фото товаров по шаблонам имён; загрузки из админки — `static/products/uploads/`
- `static/campaign/` — кадры кампании (`campaign-N.*`); загрузки из админки — `static/campaign/uploads/`

---

**Напоминание:** бинарные файлы (jpg/png) в репозиторий часто не коммитят — их нужно скопировать на свой ПК в `static/products/` и `static/campaign/`, затем при необходимости выполнить `seed_demo_content.py` или править каталог в админке. Полный снимок данных можно восстановить из бэкапа SQL (`.bak`).
