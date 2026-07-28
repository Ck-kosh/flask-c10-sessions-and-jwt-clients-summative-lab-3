# Productivity API — Flask Backend

A secure Flask REST API for managing user-owned productivity tasks. This backend uses session-based authentication with strong password hashing, task ownership enforcement, and paginated task lists.

---

## Project Description

This API allows registered users to create, read, update, and delete their own tasks. Each task belongs to a single user, and the application blocks access to tasks owned by other users.

The backend is implemented with **Flask**, **Flask-SQLAlchemy**, **Flask-Bcrypt**, **Flask-RESTful**, and **Marshmallow**.

### Key Features

- Session-based authentication: signup, login, logout, and session persistence
- Secure password hashing with bcrypt
- Task CRUD operations with ownership enforcement
- Paginated task listing
- Request validation using Marshmallow schemas
- Demo data seeding with Faker
- Test coverage via pytest

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| Flask | 2.2.2 | Web framework |
| Flask-SQLAlchemy | 3.0.3 | ORM |
| Flask-Bcrypt | 1.0.1 | Password hashing |
| Flask-RESTful | 0.3.9 | REST routing |
| Marshmallow | 3.20.1 | Validation and serialization |
| Faker | 15.3.2 | Seed data generation |
| pytest | 7.2.0 | Testing |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ck-kosh/flask-c10-sessions-and-jwt-clients-summative-lab-3.git
cd flask-productivity-api-backend
```

### 2. Install dependencies with Pipenv

```bash
pipenv install --python 3.12
```

> If Pipenv is missing: `pip install pipenv`

### 3. Activate the virtual environment

```bash
pipenv shell
```

### 4. Start the server

```bash
flask run
```

The app will automatically create the SQLite database tables on first startup.

### 5. Seed the database with sample data

```bash
python seed.py
```

This creates sample users and tasks, including a demo user with the password `demo123`.

---

## Run Instructions

### Start the development server

```bash
flask run
```

The API is available at `http://localhost:5555`.

### Run the tests

```bash
pytest -v
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/signup` | Register a new user | No |
| `POST` | `/login` | Log in and create a session | No |
| `DELETE` | `/logout` | Log out and clear session | Yes |
| `GET` | `/check_session` | Return authenticated user data | Yes |
| `GET` | `/me` | Alias for `/check_session` | Yes |

#### Signup

```json
POST /signup
{
  "username": "johndoe",
  "password": "securepass"
}
```

**Response:** `201 Created`

#### Login

```json
POST /login
{
  "username": "johndoe",
  "password": "securepass"
}
```

**Response:** `200 OK`

#### Logout

```http
DELETE /logout
```

**Response:** `204 No Content`

#### Check Session

```http
GET /check_session
```

**Response:** `200 OK` when authenticated, otherwise `401 Unauthorized`.


### Task Management (Protected Routes)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks` | List tasks for the logged-in user |
| `POST` | `/tasks` | Create a new task |
| `GET` | `/tasks/<int:id>` | Retrieve a single task |
| `PATCH` | `/tasks/<int:id>` | Update a task |
| `DELETE` | `/tasks/<int:id>` | Delete a task |

#### List Tasks

```http
GET /tasks?page=1&per_page=10
```

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

```http
GET /tasks/42
```

**Response:** `200 OK` if the task belongs to the authenticated user.

#### Update Task

```json
PATCH /tasks/42
{
  "status": "completed"
}
```

**Response:** `200 OK`

#### Delete Task

```http
DELETE /tasks/42
```

**Response:** `200 OK`

---

## Project Structure

```
flask-productivity-api-backend/
├── .flaskenv
├── Pipfile
├── Pipfile.lock
├── README.md
├── seed.py
├── test_app.py
└── server/
    ├── app.py
    ├── config.py
    ├── models.py
    └── schemas.py
```

---

## Data Model

### User

- `id` — Integer primary key
- `username` — String, unique, required
- `_password_hash` — bcrypt hash, not returned in API output
- `created_at` — DateTime

### Task

- `id` — Integer primary key
- `title` — String, required
- `description` — Text, optional
- `priority` — String, default `medium`
- `status` — String, default `pending`
- `due_date` — DateTime, optional
- `created_at` — DateTime
- `updated_at` — DateTime
- `user_id` — Integer foreign key to `users.id`

---

## Notes

- The default database is SQLite at `server/app.db`.
- Session authentication is used for protected routes.
- `seed.py` creates demo data for fast local testing.

---

## License

This project has no license.
