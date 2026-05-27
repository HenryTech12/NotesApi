# Notes API (Secure, Multi-User, Azure Aligned)

## 🌐 Live Demo

-   **Base URL:** [https://notesapi-sgvx.onrender.com](https://notesapi-sgvx.onrender.com)
-   **Interactive Docs:** [https://notesapi-sgvx.onrender.com/docs](https://notesapi-sgvx.onrender.com/docs)

## 📸 Development Progress

-   **[Day 1: Initial Setup & Auth](postman-screenshots/MINGW64__c_Users_DELL%205_25_2026%2011_16_55%20PM.png)**
-   **[Day 2: Notes CRUD & Azure Alignment](curl-screenshot-day2/MINGW64__c_Users_DELL%205_26_2026%2010_22_12%20PM.png)**
-   **[Day 3: Groq AI Integration](curl-screenshot-day3/MINGW64__c_Users_DELL%205_27_2026%208_10_41%20PM.png)**

A production-grade REST API built with FastAPI, PostgreSQL/SQLite (SQLAlchemy Async), and Alembic, strictly adhering to the **Microsoft Azure REST API Guidelines**. Now supercharged with **Groq AI** for intelligent summaries and tag suggestions.

## ✨ AI Features (New!)

This API now integrates **Groq API (Llama 3.3 70B)** to provide:
-   **Auto-Summarization:** Generates concise summaries of your notes.
-   **Smart Tagging:** Suggests relevant tags based on the note's content.
-   **Response Caching:** AI responses are cached for 1 hour to optimize performance and reduce API costs.

## �️ Architectural Resilience & Compliance

This project is built with production-grade patterns focused on reliability and security:

### 1. Error Handling & Network Resiliency
Aligned with [Azure Retry Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry), the AI integration features:
-   **Exponential Backoff**: Retries on transient errors (429, 5xx) with increasing delays.
-   **Jitter**: Randomized delays to prevent synchronized retry spikes (thundering herd).
-   **Timeout Controls**: Strict `httpx` timeouts to prevent hanging connections.

### 2. Secrets Management (12-Factor App)
Aligned with [Twelve-Factor App (III. Config)](https://12factor.net/config):
-   **Env-Var Driven**: All configuration is decoupled from code and injected via environment variables.
-   **Zero Hardcoding**: No API keys, database credentials, or JWT secrets are stored in the codebase.
-   **Secure Isolation**: `.env` is ignored by version control to prevent accidental leaks.

### 3. Database Fault Tolerance
-   **Connection Pooling**: Uses SQLAlchemy async pooling with `pool_pre_ping=True` to detect and recover from dropped DB connections automatically.

## �🚀 Setup & Run

1. **Environment Config:**
   Copy `.env.example` to `.env` and fill in your values. Make sure to include your `GROQ_API_KEY`.

    ```bash
    cp .env.example .env
    ```

2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Database Migrations:**

    ```bash
    alembic upgrade head
    ```

4. **Start the Server:**
    ```bash
    python src/main.py
    ```

## 🌐 Deployment note (Render)

This project is optimized for **Python 3.13.x**. If you encounter `greenlet` build errors (common on Python 3.14+), ensure you have a `runtime.txt` file specifying `python-3.13.1` or similar.

## 📋 API Overview

The `api-version` query parameter is **required** for all requests. Authentication uses JWT Bearer tokens.

### 🔐 Authentication Flow

1. **Register User:**

    ```bash
    curl -i -X POST "http://localhost:3000/auth/register?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"email": "user@example.com", "password": "Password123!"}'
    ```

2. **Login:**

    ```bash
    curl -i -X POST "http://localhost:3000/auth/login?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"email": "user@example.com", "password": "Password123!"}'
    ```

3. **Refresh Token:**

    ```bash
    curl -i -X POST "http://localhost:3000/auth/refresh?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"refreshToken": "your-refresh-token"}'
    ```

4. **Logout:**

    ```bash
    curl -i -X POST "http://localhost:3000/auth/logout?api-version=2024-05-25" \
         -H "Authorization: Bearer your-access-token" \
         -H "Content-Type: application/json" \
         -d '{"refreshToken": "your-refresh-token"}'
    ```

5. **Forgot Password:**

    ```bash
    curl -i -X POST "http://localhost:3000/auth/forgot-password?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"email": "user@example.com"}'
    ```

6. **Reset Password:**
    ```bash
    curl -i -X POST "http://localhost:3000/auth/reset-password?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"resetToken": "token-from-response", "newPassword": "NewPassword123!"}'
    ```

### 🗒️ Notes Management (Requires Auth)

-   **List My Notes:**

    ```bash
    curl -i -H "Authorization: Bearer <TOKEN>" "http://localhost:3000/notes?api-version=2024-05-25"
    ```

-   **Create Note:**

    ```bash
    curl -i -X POST -H "Authorization: Bearer <TOKEN>" \
         -H "Content-Type: application/json" \
         -d '{"title": "Secure Note", "body": "This is a private note.", "tags": ["private"]}' \
         "http://localhost:3000/notes?api-version=2024-05-25"
    ```

-   **Bulk Create Notes:**

    ```bash
    curl -i -X POST -H "Authorization: Bearer <TOKEN>" \
         -H "Content-Type: application/json" \
         -d '[{"title": "Note 1", "body": "Body 1"}, {"title": "Note 2", "body": "Body 2"}]' \
         "http://localhost:3000/notes/bulk?api-version=2024-05-25"
    ```

-   **Update Note (PUT):**

    ```bash
    curl -i -X PUT -H "Authorization: Bearer <TOKEN>" \
         -H "Content-Type: application/json" \
         -d '{"title": "Replaced Title", "body": "New full body content"}' \
         "http://localhost:3000/notes/{id}?api-version=2024-05-25"
    ```

-   **Partial Update (PATCH):**

    ```bash
    curl -i -X PATCH -H "Authorization: Bearer <TOKEN>" \
         -H "Content-Type: application/json" \
         -d '{"title": "New Title Only"}' \
         "http://localhost:3000/notes/{id}?api-version=2024-05-25"
    ```

-   **Delete Note:**
    ```bash
    curl -i -X DELETE -H "Authorization: Bearer <TOKEN>" \
         "http://localhost:3000/notes/{id}?api-version=2024-05-25"
    ```

### 🤖 AI-Powered Operations

-   **Generate Summary:**
    Generates a concise summary of a specific note using Llama 3.3.
    ```bash
    curl -i -X POST -H "Authorization: Bearer <TOKEN>" \
         "http://localhost:3000/notes/{id}/summary?api-version=2024-05-25"
    ```

-   **Auto-Suggest Tags:**
    Suggests relevant metadata tags based on the note's content.
    ```bash
    curl -i -X POST -H "Authorization: Bearer <TOKEN>" \
         "http://localhost:3000/notes/{id}/auto_tags?api-version=2024-05-25"
    ```

### 🛡️ Admin Features (Admin Role Only)

Admin users can manage the entire system. You can create an admin using `python scripts/create_admin.py --email admin@example.com --password "SecurePass123!"`.

-   **List All Users:**

    ```bash
    curl -i -H "Authorization: Bearer <ADMIN_TOKEN>" \
         "https://notesapi-sgvx.onrender.com/admin/users?api-version=2024-05-25"
    ```

-   **Get User Details:**

    ```bash
    curl -i -H "Authorization: Bearer <ADMIN_TOKEN>" \
         "https://notesapi-sgvx.onrender.com/admin/users/{userId}?api-version=2024-05-25"
    ```

-   **Flag a User (Suspend their access):**

    ```bash
    curl -i -X PATCH -H "Authorization: Bearer <ADMIN_TOKEN>" \
         -H "Content-Type: application/json" \
         -d '{"isFlagged": true}' \
         "https://notesapi-sgvx.onrender.com/admin/users/{userId}/flag?api-version=2024-05-25"
    ```

-   **Unflag a User (Restore their access):**

    ```bash
    curl -i -X PATCH -H "Authorization: Bearer <ADMIN_TOKEN>" \
         -H "Content-Type: application/json" \
         -d '{"isFlagged": false}' \
         "https://notesapi-sgvx.onrender.com/admin/users/{userId}/flag?api-version=2024-05-25"
    ```

-   **Change a User's Role (Upgrade to Admin):**

    ```bash
    curl -i -X PATCH -H "Authorization: Bearer <ADMIN_TOKEN>" \
         -H "Content-Type: application/json" \
         -d '{"role": "admin"}' \
         "https://notesapi-sgvx.onrender.com/admin/users/{userId}/role?api-version=2024-05-25"
    ```

-   **View ALL Notes in the System (Privacy Override):**

    ```bash
    curl -i -H "Authorization: Bearer <ADMIN_TOKEN>" \
         "https://notesapi-sgvx.onrender.com/admin/notes?api-version=2024-05-25"
    ```

-   **Delete a User (and all their notes):**
    ```bash
    curl -i -X DELETE -H "Authorization: Bearer <ADMIN_TOKEN>" \
         "https://notesapi-sgvx.onrender.com/admin/users/{userId}?api-version=2024-05-25"
    ```

## 🔄 Idempotency

| Method | Endpoint               | Idempotent | Reason                                       |
| ------ | ---------------------- | ---------- | -------------------------------------------- |
| POST   | `/auth/register`       | No         | Creates a new user record.                   |
| POST   | `/auth/login`          | No         | Generates new session/refresh tokens.        |
| POST   | `/auth/refresh`        | No         | Rotates/invalidates old tokens.              |
| POST   | `/auth/logout`         | Yes        | Revokes token state; repeats result in same. |
| POST   | `/auth/reset-password` | No         | Changes state and invalidates tokens.        |
| GET    | `/notes`               | Yes        | Only retrieves data.                         |
| PUT    | `/notes/{id}`          | Yes        | Replaces resource entirely.                  |
| DELETE | `/notes/{id}`          | Yes        | Resource removal is idempotent.              |

## 🛠️ Security Decisions

-   **Bcrypt (Work Factor 12):** Provides strong protection against brute-force attacks while maintaining acceptable performance.
-   **Short-lived Access Tokens (15min):** Minimizes the window of opportunity if a token is stolen.
-   **Refresh Token Rotation:** Every refresh issues a new token and revokes the old one, detecting potential theft if an old token is reused.
-   **Timing Attack Protection:** On login, we always perform a bcrypt verification (using a dummy hash if the email is unknown) to ensure responses take a similar amount of time.
-   **SHA-256 Hashing for Tokens:** Refresh and Reset tokens are never stored in plaintext in the database.

## 📐 Engineering Excellence

-   **SQLAlchemy Async:** Non-blocking database operations for high concurrency.
-   **Alembic Migrations:** Structured, versioned database schema evolution.
-   **Azure Compliance:** Mandatory versioning, standardized `error` envelope, and `x-ms-request-id` header injection.
-   **RBAC (Role-Based Access Control):** Admin users have elevated privileges to manage all users and notes, including account suspension (flagging), role modification, and system-wide note visibility.
-   **Automated Testing:** Robust test suite covering critical paths like JWT rotation, RBAC enforcement, and data isolation.

_Built for the IEEE x GitHub Campus Experts Codeathon._
