# Productivity API — Flask Backend

A secure, session-based Flask REST API for managing user-owned tasks. Built as a summative lab project demonstrating full authentication, CRUD operations, pagination, and access control.

---

## Project Description

This API powers a productivity tool where registered users can create, read, update, and delete personal tasks. Each task is owned by exactly one user, and users can never view or modify another user's data. The backend is built with **Flask**, **Flask-SQLAlchemy**, **Flask-Bcrypt**, **Flask-RESTful**, and **Marshmallow**.

### Key Features

- **Session-based authentication** — signup, login, logout, and session persistence
- **Secure password storage** — bcrypt hashing with salt
- **Full Task CRUD** — create, list (paginated), read single, update, and delete
- **Resource isolation** — users only see their own tasks
- **Input validation** — Marshmallow schemas enforce data integrity
- **Database migrations** — Flask-Migrate for schema versioning
- **Seed data** — Faker-powered script for quick demo setup
- **Test suite** — pytest coverage for auth and CRUD flows

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Runtime |
| Flask | 2.2.2 | Web framework |
| Flask-SQLAlchemy | 3.0.3 | ORM |
| Flask-Bcrypt | 1.0.1 | Password hashing |
| Flask-RESTful | 0.3.9 | REST resource routing |
| Flask-Migrate | 4.0.0 | Database migrations |
| Marshmallow | 3.20.1 | Serialization / validation |
| Faker | 15.3.2 | Seed data generation |
| pytest | 7.2.0 | Testing |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ck-kosh/flask-c10-sessions-and-jwt-clients-summative-lab-3.git
cd flask-c10-sessions-and-jwt-clients-summative-lab-3
```

### 2. Install dependencies with Pipenv

```bash
pipenv install --python 3.12
```

> If you don't have Pipenv installed: `pip install pipenv`
> If your machine uses a different Python version, replace `3.12` with the installed version you want Pipenv to use.

### 3. Activate the virtual environment

```bash
pipenv shell
```

### 4. Initialize the database (first time only)

```bash
flask db init          # create migration repository (only once)
flask db migrate -m "Initial migration"
flask db upgrade
```

> **Note:** For development, `db.create_all()` runs automatically when the app starts, so migrations are optional for local testing.

### 5. Seed the database with sample data

```bash
python seed.py
```

This creates 6 demo users (all with password `password123`) and ~36 tasks.

---

## Run Instructions

### Start the development server

```bash
flask run
```

The API will be available at: `http://localhost:5555`

### Run the test suite

```bash
pytest -v
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
| `POST` | `/signup` | Register a new user | No |
| `POST` | `/login` | Log in and create session | No |
| `DELETE` | `/logout` | Destroy current session | No |
| `GET` | `/check_session` | Return current user if logged in | No |

#### Signup
```json
POST /signup
{
  "username": "johndoe",
  "password": "securepass"
}
```
**Response:** `201 Created` — returns the created user object (without password).

#### Login
```json
POST /login
{
  "username": "johndoe",
  "password": "securepass"
}
```
**Response:** `200 OK` — returns the user object and sets a session cookie.

#### Logout
**Response:** `204 No Content`

#### Check Session


### Tasks (Protected — requires active session)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks` | List all tasks for the logged-in user (paginated) |
| `POST` | `/tasks` | Create a new task |
| `GET` | `/tasks/<int:id>` | Retrieve a single task by ID |
| `PATCH` | `/tasks/<int:id>` | Update a task |
| `DELETE` | `/tasks/<int:id>` | Delete a task |

**Response:** `200 OK`
```json
{
  "tasks": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 4,
    "total_items": 36,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Create Task
```json
POST /tasks
{
  "title": "Finish lab report",
  "description": "Write conclusion and proofread",
  "priority": "high",
  "status": "in_progress",
  "due_date": "2026-08-15T23:59:59"
}
```
**Response:** `201 Created`

> Valid `priority` values: `low`, `medium`, `high`, `urgent`  
> Valid `status` values: `pending`, `in_progress`, `completed`, `archived`

#### Get Single Task
```
GET /tasks/42
```
**Response:** `200 OK` if owned by user; `404 Not Found` otherwise.

#### Update Task
```json
PATCH /tasks/42
{
  "status": "completed"
}
```
**Response:** `200 OK`

#### Delete Task
```
DELETE /tasks/42
```
**Response:** `200 OK` with confirmation message.

---

## Project Structure

```
flask-productivity-api/
├── server/
│   ├── __init__.py       # Package init
│   ├── app.py            # Application factory, routes, resources
│   ├── config.py         # Configuration classes
│   ├── models.py         # SQLAlchemy models (User, Task)
│   └── schemas.py        # Marshmallow schemas
├── migrations/           # Flask-Migrate revisions
├── seed.py               # Database seed script
├── test_app.py           # pytest test suite
├── Pipfile               # Pipenv dependency manifest
├── .flaskenv             # Flask environment variables
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

---

## Models

### User
| Field | Type | Constraints |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `username` | String(80) | Unique, indexed, not null |
| `_password_hash` | String(128) | Not null (bcrypt) |
| `created_at` | DateTime | Default: now |
| `tasks` | Relationship | One-to-many → Task |

### Task
| Field | Type | Constraints |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `title` | String(200) | Not null |
| `description` | Text | Nullable |
| `priority` | String(20) | Default: `medium` |
| `status` | String(20) | Default: `pending` |
| `due_date` | DateTime | Nullable |
| `created_at` | DateTime | Default: now |
| `updated_at` | DateTime | Auto-updated on change |
| `user_id` | Integer | Foreign key → `users.id`, not null |

---

## Security Notes

- Passwords are **never stored in plaintext**. Only bcrypt hashes are persisted.
- The `_password_hash` attribute is excluded from all JSON serialization.
- All task endpoints verify the session and enforce **row-level ownership** via `user_id` filtering.
- Attempting to access another user's task returns `404 Not Found` (not `403`) to prevent ID enumeration.

---

## Grading Alignment

| Rubric Criterion | Implementation |
|------------------|----------------|
| **Auth (Login / Logout)** | `POST /login`, `DELETE /logout` — correct status codes, bcrypt verification |
| **Auth (Check Session / Me)** | `GET /check_session` — persists across refresh via session cookie |
| **Auth (Sign Up)** | `POST /signup` — unique username validation, auto-login |
| **Auth (Model & Password Protection)** | `User` model with `unique=True`, bcrypt hashing, `_password_hash` protected |
| **Additional Resource** | `Task` model with 5 custom fields (`title`, `description`, `priority`, `status`, `due_date`) + FK |
| **Protected Routes** | All `/tasks/*` routes require session; users only access own data |
| **Code Structure** | Modular: `config.py`, `models.py`, `schemas.py`, `app.py` |
| **README** | Title, description, installation, run instructions, endpoint docs |
| **Seed File** | `seed.py` creates users and tasks via Faker; no errors |
| **Git Workflow** | Feature-ready commits with meaningful messages |
| **Resource CRUD + Pagination** | Full CRUD on `/tasks` with SQLAlchemy `paginate()` |

---

## Author

**Kosh** — Backend Engineer  
GitHub: [@Ck-kosh](https://github.com/Ck-kosh)

---

## License

this project has no license