# Document App

A lightweight Django application for creating, managing, and searching text documents. Documents support bulk text replacement with version tracking, and full substring search both within a single document and across all documents.

---

## Features

- Create and retrieve documents
- Bulk text replacement with partial success and warnings
- Substring search within a single document or across all documents
- Version tracking — auto-increments on every update
- Simple, sleek frontend built with Django templates and Tailwind CSS

---

## Local Setup

**Requirements:** Python 3.9+

### 1. Clone the repository

```bash
git clone <repo-url>
cd document-app
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Run the development server

```bash
python manage.py runserver
```

The app will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Frontend Pages

| Page | URL |
|---|---|
| Home — list all documents | `/` |
| Create a document | `/new/` |
| View a document | `/documents/<id>/` |
| Edit a document | `/documents/<id>/edit/` |
| Search within a document | `/documents/<id>/search/` |
| Search across all documents | `/search/` |

---

## API Design

All API endpoints are prefixed with `/api/documents/` and return JSON.

### Design Rationale

- **No authentication** — this is a prototype intended for local use.
- **Bulk replace over single replace** — the replace endpoint accepts an array of changes to allow multiple substitutions in one request, reducing round trips. Invalid changes are skipped with warnings rather than rejecting the whole request (partial success pattern).
- **Version auto-increment** — version is managed server-side and increments on every update. Clients cannot set or override it.
- **Substring search** — search uses case-insensitive SQL `LIKE` directly on the documents table, ensuring results always reflect the latest content. Matches are returned with a snippet showing surrounding context with the matched term highlighted.

---

## API Reference

### Create a Document

**`POST /api/documents/`**

| Field | Type | Required |
|---|---|---|
| `title` | string | Yes |
| `content` | string | Yes |

```bash
curl -X POST http://127.0.0.1:8000/api/documents/ \
  -H "Content-Type: application/json" \
  -d '{"title": "My Document", "content": "Hello this is my first document!"}'
```

**Response `201`**
```json
{
  "id": 1,
  "title": "My Document",
  "content": "Hello this is my first document!",
  "version": 1,
  "created_at": "2026-03-20T10:00:00+00:00",
  "updated_at": "2026-03-20T10:00:00+00:00"
}
```

---

### Retrieve a Document

**`GET /api/documents/<id>/`**

```bash
curl http://127.0.0.1:8000/api/documents/1/
```

**Response `200`**
```json
{
  "id": 1,
  "title": "My Document",
  "content": "Hello this is my first document!",
  "version": 1,
  "created_at": "2026-03-20T10:00:00+00:00",
  "updated_at": "2026-03-20T10:00:00+00:00"
}
```

---

### Bulk Replace Text

**`PATCH /api/documents/<id>/replace-text/`**

Applies an array of search/replacement pairs to the document content in order. Valid changes are applied even if others fail — skipped changes are reported in `warnings`. Version increments on every call.

| Field | Type | Required |
|---|---|---|
| `changes` | array | Yes |
| `changes[].search` | string | Yes |
| `changes[].replacement` | string | Yes |

```bash
curl -X PATCH http://127.0.0.1:8000/api/documents/1/replace-text/ \
  -H "Content-Type: application/json" \
  -d '{
    "changes": [
      {"search": "Hello", "replacement": "Hi"},
      {"search": "first", "replacement": "second"}
    ]
  }'
```

**Response `200`**
```json
{
  "id": 1,
  "title": "My Document",
  "content": "Hi this is my second document!.",
  "version": 2,
  "created_at": "2026-03-20T10:00:00+00:00",
  "updated_at": "2026-03-20T10:05:00+00:00",
  "warnings": []
}
```

**Response with warnings** (partial success)
```json
{
  "id": 1,
  "content": "Hi this is my second document!",
  "version": 2,
  "warnings": [
    "Search term \"foo\" not found in document — skipped"
  ]
}
```

---

### Search Within a Document

**`GET /api/documents/<id>/search/?q=<query>`**

Returns a snippet of content surrounding the first match, with the matched term wrapped in `>>>` and `<<<`.

```bash
curl "http://127.0.0.1:8000/api/documents/1/search/?q=document"
```

**Response `200`**
```json
{
  "id": 1,
  "query": "document",
  "snippet": "Hi this is my second >>>document<<<!"
}
```

**Response `404`** — query not found
```json
{
  "error": "\"document\" not found in document"
}
```

---

### Search Across All Documents

**`GET /api/documents/search/?q=<query>`**

Returns all documents containing the query as a substring, each with a highlighted snippet.

```bash
curl "http://127.0.0.1:8000/api/documents/search/?q=document"
```

**Response `200`**
```json
{
  "query": "document",
  "results": [
    {
      "id": 1,
      "snippet": "Hi this is my second >>>document<<<!"
    },
    {
      "id": 2,
      "snippet": "I also wrote this >>>document<<<."
    }
  ]
}
```

---

## Running Tests

```bash
python manage.py test documents.tests
```

There are 31 tests covering document creation, retrieval, bulk replacement, and search.
