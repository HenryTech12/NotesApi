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

Every request requires the `api-version` query parameter.

### Example Usage

```bash
# List notes with pagination and filtering
curl "http://localhost:3000/notes?api-version=2024-05-25&top=5&skip=0"

# Create a new note
curl -X POST "http://localhost:3000/notes?api-version=2024-05-25" \
     -H "Content-Type: application/json" \
     -d '{"title": "Pro Tip", "body": "Always use Pydantic for validation.", "tags": ["coding"]}'
```

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
