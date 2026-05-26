# Notes API (Secure, Multi-User, Azure Aligned)

## 🌐 Live Demo

-   **Base URL:** [https://notesapi-sgvx.onrender.com](https://notesapi-sgvx.onrender.com)
-   **Interactive Docs:** [https://notesapi-sgvx.onrender.com/docs](https://notesapi-sgvx.onrender.com/docs)

A production-grade REST API built with FastAPI, PostgreSQL (SQLAlchemy Async), and Alembic, strictly adhering to the **Microsoft Azure REST API Guidelines**.

## 🚀 Setup & Run

1. **Environment Config:**
   Copy `.env.example` to `.env` and fill in your values.

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
-   **RBAC:** Admin users have elevated privileges to manage all users and notes.

_Built for the IEEE x GitHub Campus Experts Codeathon._
