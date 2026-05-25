# Production-Grade Notes REST API (FastAPI)

A robust, production-ready Notes API built with Python and FastAPI for the IEEE x GitHub Campus Experts 10-Day Codeathon. This version emphasizes type safety, high performance, and standard engineering practices.

## 🚀 Tech Stack

- **Runtime:** Python 3.9+
- **Framework:** FastAPI
- **Validation:** Pydantic v2
- **Server:** Uvicorn
- **ID Generation:** UUID v4

## 🛠️ Setup & Run

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Server:**
   ```bash
   python src/main.py
   ```
   *Or using uvicorn directly:*
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload
   ```

The server will be running at `http://localhost:3000`.

## 📌 API Endpoints

Base Path: `/api/v1`

### Health Check
- `GET /health` - Check if the API is alive.

### Notes CRUD
- `POST /notes` - Create a new note.
- `GET /notes` - List all notes (supports pagination/sorting/filtering).
- `GET /notes/:id` - Get a specific note.
- `PUT /notes/:id` - Replace an entire note.
- `PATCH /notes/:id` - Partially update a note.
- `DELETE /notes/:id` - Delete a note.

## 🔍 Query Parameters (`GET /notes`)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `page` | `1` | Page number. |
| `limit` | `10` | Notes per page (Min: 1, Max: 100). |
| `sort` | `createdAt` | Sort by `createdAt`, `updatedAt`, or `title`. |
| `order` | `desc` | `asc` or `desc`. |
| `tag` | - | Filter by a specific tag (exact match). |
| `search` | - | Case-insensitive search in `title` and `body`. |

## 📡 CURL Examples

### Create a Note
```bash
curl -X POST http://localhost:3000/api/v1/notes \
-H "Content-Type: application/json" \
-d '{"title": "FastAPI Power", "body": "Building APIs with Pydantic is amazing.", "tags": ["python", "fastapi"]}'
```

### List Notes (Sorted by Title)
```bash
curl "http://localhost:3000/api/v1/notes?sort=title&order=asc"
```

### Delete a Note
```bash
curl -X DELETE http://localhost:3000/api/v1/notes/<id>
```

## 🧠 Engineering Standards Applied

- **Type Safety:** Full Pydantic schemas for request and response validation.
- **Custom Exception Handling:** Centralized handlers to ensure consistent error shapes even for 422 errors.
- **ANSI Logging:** Middleware for color-coded request logging.
- **Immutability:** Immutable `id` and `createdAt` fields.
- **Auto-Documentation:** Interactive Swagger UI available at `/docs`.

---
*Built for the IEEE x GitHub Campus Experts Codeathon.*
