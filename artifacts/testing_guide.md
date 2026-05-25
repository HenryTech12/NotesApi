# API Testing Guide - Azure Aligned Notes API

All requests require the `api-version=2024-05-25` query parameter.

## 1. Success Scenarios

### Health Check

```bash
curl -X GET "http://localhost:3000/health?api-version=2024-05-25" -v
```

### Create a single Note

```bash
curl -X POST "http://localhost:3000/notes?api-version=2024-05-25" \
     -H "Content-Type: application/json" \
     -H "x-ms-client-request-id: my-local-id-001" \
     -d '{
       "title": "Strategy Meeting",
       "body": "Discuss the Azure migration plan for the Q3 roadmap.",
       "tags": ["work", "azure"]
     }'
```

### List Notes (with Filtering & Pagination)

```bash
# Get top 2 results tagged 'work'
curl -X GET "http://localhost:3000/notes?api-version=2024-05-25&top=2&filter=tag eq 'work'"
```

### Bulk Import

```bash
curl -X POST "http://localhost:3000/notes/bulk?api-version=2024-05-25" \
     -H "Content-Type: application/json" \
     -d @artifacts/bulk_notes_data.json
```

### Partial Update (PATCH)

Replace `{id}` with a real ID from the list:

```bash
curl -X PATCH "http://localhost:3000/notes/{id}?api-version=2024-05-25" \
     -H "Content-Type: application/json" \
     -d '{"title": "Updated Title Only"}'
```

---

## 2. Error Scenarios (Azure Error Format)

### Missing API Version (400 Bad Request)

```bash
curl -X GET "http://localhost:3000/notes"
```

**Expected Response:**

```json
{
    "error": {
        "code": "InvalidRequest",
        "message": "The api-version query parameter (?api-version=) is required for all requests"
    }
}
```

### Validation Error (400 Bad Request)

Triggering a "body too short" error:

```bash
curl -X POST "http://localhost:3000/notes?api-version=2024-05-25" \
     -H "Content-Type: application/json" \
     -d '{"title": "Oops", "body": "no"}'
```

**Expected Response:**

```json
{
    "error": {
        "code": "InvalidRequest",
        "message": "The request is invalid.",
        "details": [
            {
                "code": "InvalidField",
                "target": "body",
                "message": "String should have at least 3 characters"
            }
        ]
    }
}
```

### Resource Not Found (404 Not Found)

```bash
curl -X GET "http://localhost:3000/notes/invalid-uuid?api-version=2024-05-25"
```

**Expected Response:**

```json
{
    "error": {
        "code": "ResourceNotFound",
        "message": "Note with id invalid-uuid not found."
    }
}
```

### Empty PATCH Payload (400 Bad Request)

```bash
curl -X PATCH "http://localhost:3000/notes/{id}?api-version=2024-05-25" \
     -H "Content-Type: application/json" \
     -d '{}'
```
