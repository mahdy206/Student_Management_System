# Student Management System

A secure, production-ready REST API built with **FastAPI** for managing university students, featuring JWT authentication, role-based access control, Redis caching, structured logging, a monitoring dashboard, a full frontend UI, and Docker support.

---

## Team Members

| Name | Role |
|------|------|
| Haitham| Backend Lead – Auth, JWT, Database |
| [Member 2] | Student Routes & Services |
| [Member 3] | Caching, Logging & Monitoring |
| [Member 4] | Testing & Documentation |

---

## Features

- **JWT Authentication** – Register, login, and secure token-based access
- **Role-Based Authorization** – Admin vs Student permissions
- **Full CRUD** – Create, read, update, delete students
- **Advanced Filtering** – Filter by department and minimum GPA
- **Pagination** – Configurable page size and number
- **Redis Caching** – Cache-Aside pattern with automatic invalidation
- **Structured Logging** – File + terminal logs via Loguru
- **Monitoring Dashboard** – Live request/error metrics at `/monitoring/dashboard`
- **API Testing** – Comprehensive pytest test suite with 20+ test cases
- **Frontend UI** – Full HTML/CSS/JS interface for all CRUD operations
- **Docker Support** – One-command startup with Docker Compose

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| Database | SQLite (Docker/dev) / SQL Server (local) |
| ORM | SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt |
| Caching | Redis |
| Logging | Loguru |
| Testing | pytest + httpx |
| Frontend | HTML / CSS / JavaScript |
| Container | Docker + Docker Compose |

---

## Project Structure

```
Code/
├── App/
│   ├── Auth/
│   │   ├── Jwt.py              # Token creation & validation
│   │   └── Password.py         # bcrypt hashing
│   ├── Models/
│   │   ├── User.py             # User ORM model
│   │   ├── Student.py          # Student ORM model
│   │   └── __init__.py
│   ├── Schemas/
│   │   ├── User.py             # Pydantic schemas for User
│   │   └── Student.py          # Pydantic schemas for Student
│   ├── Routes/
│   │   ├── Auth.py             # /auth endpoints
│   │   ├── Students.py         # /students endpoints
│   │   └── Monitoring.py       # /monitoring dashboard
│   ├── Services/
│   │   └── Student_service.py  # Business logic & caching
│   ├── Utils/
│   │   ├── Cache.py            # Redis helpers
│   │   └── Logger.py           # Loguru setup
│   ├── Database.py             # DB engine & session
│   └── Main.py                 # App entrypoint + middleware
├── Tests/
│   ├── conftest.py             # Shared fixtures & test DB setup
│   ├── Test_auth.py            # Auth endpoint tests (10 tests)
│   └── Test_students.py        # Student CRUD + edge case tests (20 tests)
├── frontend/
│   └── index.html              # Full SPA frontend
├── logs/
│   ├── app.log                 # General logs (rotated daily, 7 days)
│   └── errors.log              # Error-only logs (rotated weekly)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Option A — Run with Docker (Recommended)

This is the easiest way. Docker handles the database, Redis, and the API automatically.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/your-org/student-management-system.git
cd student-management-system
```

**2. Build and start all services**
```bash
docker compose up --build
```

That's it. Docker will:
- Build the FastAPI image
- Start a Redis container
- Start the API connected to both

**3. Access the application**

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:8000/app |
| API Docs (Swagger) | http://localhost:8000/docs |
| Monitoring Dashboard | http://localhost:8000/monitoring/dashboard |
| API Root | http://localhost:8000 |

**4. Stop the application**
```bash
docker compose down
```

To also remove stored data:
```bash
docker compose down -v
```

---

## Option B — Run Locally (Manual Setup)

### Prerequisites
- Python 3.10+
- Redis running locally
- Microsoft SQL Server + ODBC Driver 17 *(or use SQLite by setting DATABASE_URL)*

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/your-org/student-management-system.git
cd student-management-system
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment**

Create a `.env` file in the project root (optional — defaults work for local SQL Server):
```env
SECRET_KEY=your_secret_key_here
REDIS_URL=redis://localhost:6379
# Uncomment to use SQLite instead of SQL Server:
# DATABASE_URL=sqlite:///./student_management.db
```

**4. Start Redis**
```bash
# Linux / macOS
redis-server

# Windows (via WSL or Memurai)
memurai
```

**5. Run the application**
```bash
uvicorn App.Main:app --reload
```

The API will be available at **http://127.0.0.1:8000**

---

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Login and get JWT token | No |

### Students

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| GET | `/students/` | Get all students (filters + pagination) | Any logged-in user |
| GET | `/students/{id}` | Get student by ID | Any (students see own only) |
| POST | `/students/` | Create a new student | Admin only |
| PUT | `/students/{id}` | Update student | Admin or own profile |
| DELETE | `/students/{id}` | Delete student | Admin only |

**Query Parameters for `GET /students/`:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `department` | string | — | Filter by department name |
| `min_gpa` | float (0–4) | — | Filter by minimum GPA |
| `page` | int ≥ 1 | 1 | Page number |
| `size` | int 1–100 | 10 | Results per page |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/monitoring/dashboard` | Live HTML monitoring dashboard |
| GET | `/monitoring/stats` | JSON metrics (requests, errors, avg response time) |

---

## Authentication Usage

### 1. Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@university.com", "password": "securepass", "role": "admin"}'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@university.com", "password": "securepass"}'
# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Use token in requests
```bash
curl http://localhost:8000/students/ \
  -H "Authorization: Bearer eyJ..."
```

---

## Running Tests

Tests use an isolated SQLite database and never touch the real database.

```bash
# Run all tests
pytest Tests/ -v

# Run only auth tests
pytest Tests/Test_auth.py -v

# Run only student tests
pytest Tests/Test_students.py -v

# Run with coverage report
pytest Tests/ -v --tb=short
```

**Test coverage includes:**
- User registration (valid, duplicate email, invalid email, invalid role)
- Login (success, wrong password, nonexistent user)
- Protected route access (no token, invalid token)
- GET all students (auth required, department filter, GPA filter, pagination)
- GET student by ID (admin access, not found, student privacy restriction)
- POST create student (admin only, student forbidden, duplicate email, missing fields, invalid GPA)
- PUT update student (admin updates any, partial updates, student cannot update others, not found)
- DELETE student (admin can delete, student forbidden, not found, cascade verification)
- Monitoring endpoints

---

## Caching Strategy

The system uses the **Cache-Aside** pattern with Redis:

| Operation | Cache Key | TTL | Action |
|-----------|-----------|-----|--------|
| GET all | `students:all:{dept}:{gpa}:{page}:{size}` | 5 min | Read from cache or DB |
| GET by ID | `students:{id}` | 5 min | Read from cache or DB |
| POST | — | — | Invalidates all `students:all:*` keys |
| PUT | — | — | Invalidates `students:{id}` + all `students:all:*` |
| DELETE | — | — | Invalidates `students:{id}` + all `students:all:*` |

Redis errors are handled gracefully — the app continues working even if Redis is unavailable.

---

## Logging

Logs are written to two files in the `logs/` directory:

| File | Content | Rotation |
|------|---------|----------|
| `logs/app.log` | All requests, auth events, CRUD operations | Daily, kept 7 days |
| `logs/errors.log` | Errors and exceptions only | Weekly |

**Logged events include:**
- Every HTTP request: method, path, status code, response time
- Auth events: user registration, login success, failed login attempts
- CRUD operations: student created, updated, deleted (with actor)
- Cache hits and misses
- Unhandled exceptions with full traceback

---

## Roles & Permissions

| Action | Admin | Student |
|--------|-------|---------|
| View all students | ✅ | ✅ |
| View own profile | ✅ | ✅ |
| View other profiles | ✅ | ❌ (403) |
| Create student | ✅ | ❌ (403) |
| Update own profile | ✅ | ✅ |
| Update other profiles | ✅ | ❌ (403) |
| Delete student | ✅ | ❌ (403) |

---

## Frontend

The frontend is a single-page application served at `/app`.

**Features:**
- Login and registration forms with validation
- Student table with department and GPA filters
- Pagination controls
- Admin: Add, edit, and delete students via modal forms
- Student: View-only mode (sees all students, cannot modify)
- GPA color-coded badges (green ≥ 3.5, amber ≥ 2.5, red < 2.5)
- Toast notifications for all actions
- Persistent login via localStorage

---

## Interactive API Docs

FastAPI provides auto-generated documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
