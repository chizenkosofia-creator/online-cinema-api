
# Online Cinema

Async REST API for an online cinema: movie catalog, shopping cart, orders and Stripe payments.

Built with FastAPI, PostgreSQL, SQLAlchemy 2.0 (async), Alembic, Celery, Docker, and Poetry.

---

## Quick start

1. Clone the repository and navigate to the project folder:
   ```bash
   git clone [https://github.com/chizenkosofia-creator/online-cinema-api.git](https://github.com/chizenkosofia-creator/online-cinema-api.git)
   cd online-cinema-api

```

2. Create and configure your environment variables:
```bash
cp .env.example .env

```


3. Build and launch all services using Docker Compose:
```bash
docker compose up --build -d

```


4. Run database migrations:
```bash
docker compose exec app alembic upgrade head

```



* **API docs (Swagger):** http://localhost:8000/docs (Protected via Basic Auth)
* **Health check:** http://localhost:8000/health
* **Mailpit (Local inbox for outgoing emails):** http://localhost:8025

---

## ️ Services

The project is fully containerized and runs using Docker Compose. It includes the following services:

| Service | Container Name | Purpose |
| :--- | :--- | :--- |
| `db` | `cinema_db` | **PostgreSQL 15** database for storing users, movies, orders, and payments (with healthcheck) |
| `redis` | `cinema_redis` | **Redis 7** message broker and cache for Celery background tasks |
| `minio` | `cinema_minio` | **MinIO S3**-compatible storage for uploading media files (such as user avatars) |
| `web` | `cinema_web` | **FastAPI** web application (available on port `8000`), handling the core API logic |
| `celery` | `cinema_celery` | **Celery Worker** for executing asynchronous background tasks (sending emails, clearing tokens) |
### Managing Celery Logs & Restarts

To view worker and beat logs:
```bash
docker compose logs -f celery

```

*Note: Unlike the FastAPI app (`app`), the worker and beat do not auto-reload on code changes. Restart them after modifying tasks or schedules:*

```bash
docker compose restart celery_worker celery_beat

```

---

##  Running Tests

Tests require a running PostgreSQL instance. A separate test database (`<POSTGRES_DB>_test`) is created automatically on every test run, keeping your development data safe. Redis is not required (Celery tasks are mocked).

* **Inside Docker:**
```bash
docker compose exec app pytest -v

```


* **Locally:**
```bash
docker compose up -d db
poetry run pytest -v

```


* **With a coverage report:**
```bash
poetry run pytest --cov=src --cov-report=term-missing

```



---

##  Local Development (Without Docker for the App)

```bash
# 1. Install Python dependencies
poetry install

# 2. Start infrastructure services
docker compose up -d db redis mailpit

# 3. Apply database migrations
poetry run alembic upgrade head

# 4. Start the FastAPI development server
poetry run uvicorn src.main:app --reload

```

In separate terminal windows, start the background workers:

```bash
# Terminal 2: Celery worker (--pool=solo required on Windows)
poetry run celery -A src.core.celery_app worker --loglevel=info --pool=solo

# Terminal 3: Celery beat (for periodic tasks)
poetry run celery -A src.core.celery_app beat --loglevel=info

```

> **Windows Tip:** Keep `POSTGRES_HOST=127.0.0.1` in your `.env` file. Using `localhost` can cause database connection delays due to IPv6 fallback attempts.

---

##  API Endpoints Overview

### Accounts

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/accounts/register` | Register a new inactive user and trigger an activation email (token valid for 24h) |
| `POST` | `/accounts/activate` | Activate account using email and token |
| `POST` | `/accounts/resend-activation` | Resend activation email if expired |

> *Password requirements:* Must be at least 8 characters long and contain uppercase, lowercase letters, digits, and special characters.

### Catalog, Orders & Payments

* Full CRUD operations for movies, genres, stars, and directors with filtering, sorting, and pagination.
* Secure cart management, order placement with historical price snapshot (`price_at_order`), and status tracking (`pending`, `paid`, `canceled`).
* Integrated **Stripe Checkout Sessions** and webhook listeners for seamless payment handling.

Full request/response schemas, payload specifications, and query parameters are fully documented in the interactive Swagger UI.

---

## Project Structure

```text
src/
  accounts/      # Authentication, registration, tokens, and user management
  admin/         # Admin panel and administrative tools
  config/        # Application settings and configurations
  movies/        # Movie catalog, genres, stars, directors, and reviews
  orders/        # Cart, order placement, and order lifecycle management
  payments/      # Stripe integration and payment processing
  security/      # JWT tokens, password hashing, and permissions
  validators/    # Custom input and password complexity validators
alembic/         # Database migration scripts
tests/           # Pytest test suite (mirroring src/ structure)

```

---

## Features Checklist

* [x] User registration & account activation via email
* [x] JWT authentication (Access & Refresh tokens) and role management (`User`, `Moderator`, `Admin`)
* [x] Password management (change and reset)
* [x] Movies: catalog, search, sorting, filtering, and moderator CRUD
* [x] Shopping cart & Orders lifecycle
* [x] Secure Payments via Stripe & Webhooks
* [x] Automated testing suite with pytest and code coverage tracking

```

```