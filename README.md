# Аренда вещей (Flask)

Веб-приложение: каталог, корзина, профиль пользователя, аренды, админка. Бэкенд: **Python / Flask**, база данных: **PostgreSQL** (обычно **Supabase**). Медиа по желанию — **Supabase Storage** или статика.

## Быстрый старт (PowerShell)

Из папки `rental_app`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Заполните в .env POSTGRES_CONNECTION_STRING (строка из Supabase: Settings → Database)
python scripts/init_postgres_db.py
python app.py
```

Сайт: **http://127.0.0.1:5000**

При первом клонировании без `.env` приложение при импорте попытается подключиться к БД для применения схемы — задайте строку подключения до запуска или сразу после копирования `.env.example`.

---

## Что установить

- **Python 3.10+** (рекомендуется 3.11+)
- Проект **PostgreSQL**: бесплатно удобно через **[Supabase](https://supabase.com)** (создайте проект, возьмите строку подключения `postgres://...` или `postgresql://...` для **соединений с приложения**, не pooling-only URI, если драйвер ругается — используйте вариант с **Session mode / direct** из документации Supabase)

Для **локальной** PostgreSQL достаточно собрать обычный URL подключения для `psycopg2`.

**Не нужно:** SQL Server, pyodbc, ODBC Driver — в текущей версии не используются.

---

## Конфигурация (`.env`)

Скопируйте **`.env.example`** → **`.env`** и заполните. Секреты в репозиторий не коммитьте.

| Переменная | Назначение |
|------------|------------|
| `POSTGRES_CONNECTION_STRING` или `DATABASE_URL` / `SUPABASE_DB_URL` | Подключение к PostgreSQL (обязательно для работы приложения). |
| `SMTP_*`, `PICKUP_ADDRESS` | Локально: отправка писем (верификация, оповещения о заказе). См. `.env.example`. |
| `EMAIL_DELIVERY_DISABLED=1` | На хостинге (например Render): не слать почту; регистрация без письма (автоверификация в коде). |
| `RESEND_API_KEY`, `RESEND_FROM` | Опционально: альтернатива SMTP через HTTP API. |
| `DEMO_MODE=1` | Включает демо-вход по ролям (если поддерживается в приложении). |
| `SUPABASE_*` | Опционально: загрузка медиа в Storage и публичные URL для слайдов/видео. |

---

## Зависимости Python

```bash
pip install -r requirements.txt
```

Состав: Flask, psycopg2-binary, python-dotenv, requests, deep-translator, gunicorn (для продакшена).

---

## Инициализация схемы и демо-данных

Скрипт создаёт/проверяет таблицы (через `core/pg_schema.py`) и при **пустом** каталоге заливает стартовый набор из `seed_defaults.py` (бренды, товары, кампания и т.д.).

```bash
python scripts/init_postgres_db.py
```

**Полный пересбор демо-каталога** (очистить товары/зависимые строки и залить снова):

```powershell
$env:SEED_RESET_DEMO = "1"
python scripts/init_postgres_db.py
```

Локальные фото можно по-прежнему класть в `static/products/` и `static/campaign/` согласно правилам в `seed_defaults.py` (раздел ниже сохранён по смыслу).

---

## Локальные фото (`static/products/`, `static/campaign/`)

Имена для демо-артикулов (расширения `png`, `jpg`, …):

| Артикул | Шаблон имён файлов |
|---------|---------------------|
| `RO-0001` | `kiss-heels-1`, `kiss-heels-2`, … |
| `RS-0001` | `raf-bomber-1`, … |
| `YZY-9999` | `yzy-1`, … |
| `BAL-0001` | `balenciaga-1`, … |
| `BC-0001` | `couturebag.jpg` или `couturebag-1.png`, … |

**Кампания:** файлы вида **`campaign-<номер>.<расширение>`** в `static/campaign/`.

На главной и `/collection` для RTW есть фильтры: поиск, бренд, состояние, цена и т.д. Страница **Поиск** ищет по каталогу.

---

## Запуск

```bash
python app.py
```

Альтернатива:

```powershell
$env:FLASK_APP = "app.py"
flask run --port 5000
```

**Продакшен (например Render):** `gunicorn` и переменные окружения там же; пример см. у провайдера (команда вроде `gunicorn app:app --bind 0.0.0.0:$PORT`).

---

## Регистрация, почта и админка

- Регистрация с подтверждением по email при работающем SMTP (или через Resend, если настроено).
- С `EMAIL_DELIVERY_DISABLED=1` письма не уходят, верификация для новых пользователей обходится программно — удобно на бесплатном хостинге без исходящего SMTP.
- Админка: `/admin/login`; доступ только у пользователей с `is_admin=1`.
- В админке: товары, бренды, заказы, пользователи, кампания. При подтверждении заказа может уходить письмо клиенту (если почта включена).

## Уровни и member area

- Уровень по гибридной модели: число возвращённых аренд + суммарные траты.
- Пороги в `core/constants.py` (`LOYALTY_LEVELS`).

## Media storage

- Загрузки из админки могут сохраняться в **Supabase Storage** (в БД хранятся URL).
- Если Supabase не задан — используются локальные пути/`static`.

---

## Один аккаунт: локально и на хосте

Если у **локального** `POSTGRES_CONNECTION_STRING` и у **деплоя** одна и та же база Supabase, заказы и статусы видны всем клиентам сразу после обновления страницы. Разные базы — разные данные.

---

## Чеклист «развернуть у себя»

1. Python 3.10+, клонировать репозиторий.
2. `python -m venv .venv` → активировать.
3. `pip install -r requirements.txt`
4. `copy .env.example .env`, заполнить **`POSTGRES_CONNECTION_STRING`** (и при необходимости SMTP / Supabase Storage).
5. `python scripts/init_postgres_db.py`
6. (Опционально) положить свои файлы в `static/products/` и `static/campaign/`, при необходимости перезапустить сид с `SEED_RESET_DEMO=1`.
7. `python app.py`

---

## Структура проекта (кратко)

| Путь | Назначение |
|------|------------|
| `app.py` | Точка входа Flask, регистрация роутов, контекст шаблонов |
| `core/config.py` | Настройки из переменных окружения и `.env` |
| `core/db.py` | Пул подключений PostgreSQL (`psycopg2`), `get_db_connection` |
| `core/pg_schema.py` | DDL таблиц для PostgreSQL |
| `core/catalog.py` | Каталог, связанные товары |
| `core/rental_orders.py` | Заказы, чекаут, админские выборки, статистика дашборда |
| `core/account_service.py`, `session_cart.py`, `auth`-логика в `routes/` | Пользователь, сессия, корзина |
| `routes/public.py`, `auth.py`, `admin.py`, `api.py` | Маршруты |
| `services/rental_service.py` | Даты аренды, проверки доступности батчем |
| `repositories/` | `user_repository`, `order_repository` — точечный доступ к БД |
| `scripts/init_postgres_db.py` | Схема + первичное наполнение |
| `seed_defaults.py` | Демо-товары, кампания, fallback URL |
| `templates/`, `static/` | Шаблоны и статика |

---

**Напоминание:** большие бинарники в Git часто не кладут — скопируйте нужные медиа в `static/` или загрузите через админку в Supabase; `.env` с паролями не коммитьте (добавьте в `.gitignore`, если ещё нет).
