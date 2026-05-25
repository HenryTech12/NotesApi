# Notes API (Microsoft Azure Aligned)

A production-grade REST API built with FastAPI, strictly adhering to the **Microsoft Azure REST API Guidelines**.

## 🚀 Setup & Run

1. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2. **Start the Server:**

    ```bash
    python src/main.py
    ```

3. **Run Tests:**
    ```bash
    PYTHONPATH=$PWD pytest -v
    ```

## 📋 API Overview

The `api-version` query parameter is optional (defaults to `2024-05-25`).

### Example Usage & Testing

To test the API and capture "screenshots" for your submission, run these commands in your terminal while the server is active:

1. **Health Check** (Verifies connectivity):

    ```bash
    curl -i "http://localhost:3000/health?api-version=2024-05-25"
    ```

2. **List Notes** (Shows pagination & Azure headers):

    ```bash
    curl -i "http://localhost:3000/notes?api-version=2024-05-25&top=2"
    ```

3. **Create Note** (Tests validation & creation):
    ```bash
    curl -i -X POST "http://localhost:3000/notes?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"title": "Submission Note", "body": "API is fully functional and compliant."}'
    ```

**How to provide screenshots:**

-   Open your terminal (Command Prompt, PowerShell, or Bash).
-   Run one of the `curl` commands above.
-   Take a screenshot of the **Terminal window** ensuring both the `curl` command and the JSON response (along with the HTTP headers from `-i`) are clearly visible.

| Method | Endpoint      | Description                                   |
| ------ | ------------- | --------------------------------------------- |
| GET    | `/notes`      | List with `top`, `skip`, `filter`, `orderby`. |
| POST   | `/notes`      | Create a new note.                            |
| POST   | `/notes/bulk` | Ingest multiple notes.                        |
| GET    | `/notes/{id}` | Retrieve a specific note.                     |
| PATCH  | `/notes/{id}` | Partially update a note.                      |
| PUT    | `/notes/{id}` | Replace a note entirely.                      |
| DELETE | `/notes/{id}` | Remove a note (204 No Content).               |

## 🛠️ Engineering Excellence

-   **Azure Compliance**: Mandatory versioning, standardized error envelopes, and `x-ms-request-id` header injection.
-   **Advanced Querying**: Support for OData-style filters and absolute `nextLink` pagination.
-   **Observability**: Custom ANSI color-coded middleware for terminal-based request tracking.

Detailed `curl` examples for success and error states are available in [artifacts/testing_guide.md](artifacts/testing_guide.md).

## 🧪 Testing & Seed Data

## The application automatically boots up with **3 pre-seeded notes** via \`store.seed()\`. This allows judges and developers to immediately test pagination, sorting, and filtering parameters without manually creating data first.

_Built for the IEEE x GitHub Campus Experts Codeathon._
