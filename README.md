# Notes API (Microsoft Azure Aligned)

## 🌐 Live Demo

-   **Base URL:** [https://notesapi-sgvx.onrender.com](https://notesapi-sgvx.onrender.com)
-   **Interactive Docs:** [https://notesapi-sgvx.onrender.com/docs](https://notesapi-sgvx.onrender.com/docs)

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
    curl -i "https://notesapi-sgvx.onrender.com/health?api-version=2024-05-25"
    ```

2. **List Notes** (Shows pagination & Azure headers):

    ```bash
    curl -i "https://notesapi-sgvx.onrender.com/notes?api-version=2024-05-25&top=2"
    ```

3. **Create Note** (Tests validation & creation):
    ```bash
    curl -i -X POST "https://notesapi-sgvx.onrender.com/notes?api-version=2024-05-25" \
         -H "Content-Type: application/json" \
         -d '{"title": "Submission Note", "body": "API is fully functional and compliant."}'
    ```

**Screenshots:**
High-resolution screenshots showing the request/response cycle for each endpoint can be found in the [postman-screenshots/](postman-screenshots/) directory.

| Method | Endpoint      | Description                                   | Status Code |
| ------ | ------------- | --------------------------------------------- | ----------- |
| GET    | `/notes`      | List with `top`, `skip`, `filter`, `orderby`. | 200 OK      |
| POST   | `/notes`      | Create a new note.                            | 201 Created |
| POST   | `/notes/bulk` | Ingest multiple notes.                        | 201 Created |
| GET    | `/notes/{id}` | Retrieve a specific note.                     | 200 OK      |
| PATCH  | `/notes/{id}` | Partially update a note.                      | 200 OK      |
| PUT    | `/notes/{id}` | Replace a note entirely.                      | 200 OK      |
| DELETE | `/notes/{id}` | Remove a note.                                | 200 OK      |

## 🔄 Idempotency

As per [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Glossary/Idempotent), an idempotent HTTP method is one that can be called many times without different outcomes.

| Method | Idempotent | Reason                                                                             |
| ------ | ---------- | ---------------------------------------------------------------------------------- |
| GET    | Yes        | Safe method; only retrieves data.                                                  |
| PUT    | Yes        | Replacing a resource with the same data multiple times results in the same state.  |
| DELETE | Yes        | Deleting a resource results in the same final state (resource gone).               |
| PATCH  | Yes        | This implementation is idempotent; sending the same PATCH produces the same state. |
| POST   | No         | Multiple POST calls will create multiple separate resources.                       |

## 🛠️ Engineering Excellence

-   **Azure Compliance**: Mandatory versioning, standardized error envelopes, and `x-ms-request-id` header injection.
-   **Advanced Querying**: Support for OData-style filters and absolute `nextLink` pagination.
-   **Observability**: Custom ANSI color-coded middleware for terminal-based request tracking.

👉 **[Full cURL Testing Guide (Successes & Errors) →](artifacts/testing_guide.md)**

Detailed `curl` examples for success and error states are available in [artifacts/testing_guide.md](artifacts/testing_guide.md).

## 🧪 Testing & Seed Data

## The application automatically boots up with **3 pre-seeded notes** via \`store.seed()\`. This allows judges and developers to immediately test pagination, sorting, and filtering parameters without manually creating data first.

_Built for the IEEE x GitHub Campus Experts Codeathon._
