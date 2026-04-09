# Document App

A Django application for creating, managing, and redlining text documents — similar to Microsoft Word's Track Changes. Documents support occurrence-based find & replace, a full change log with accept/reject, semantic search powered by a local AI model, and substring search within and across documents.

---

## Features

- Create and retrieve documents
- Find & replace — target a specific occurrence of a word or phrase, not just all of them
- Track Changes — every replacement is logged and can be accepted or rejected
- Semantic search — find passages by meaning, not just exact keywords, toggled in the edit panel
- Cross-document search with jump to edit
- Version tracking — auto-increments on every update
- Frontend built with Django templates and Tailwind CSS

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
pip install django sentence-transformers
```

> The first time semantic search is used, the app will download the `all-MiniLM-L6-v2` model (~80MB). This only happens once and is cached automatically.

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
| View a document (Normal / Track Changes) | `/documents/<id>/` |
| Edit a document (Find & Replace / Semantic Search) | `/documents/<id>/edit/` |
| Search across all documents | `/search/` |

---

## API Design

All API endpoints are prefixed with `/api/documents/` and return JSON.

### Design Rationale

- **No authentication** — this is a prototype intended for local use.
- **Occurrence-based replacement** — the replace endpoint accepts an optional `occurrence` index so callers can target a specific instance of a word (e.g. the 2nd "the") rather than replacing all of them.
- **Track changes** — every replacement is recorded as a `DocumentChange` entry with the original text, replacement, and position. Changes can be accepted (removes the log entry) or rejected (reverts the content).
- **Version auto-increment** — version is managed server-side and increments on every update. Clients cannot set or override it.
- **Substring search** — search uses case-insensitive SQL `LIKE` directly on the documents table, ensuring results always reflect the latest content. All matches are returned with position, occurrence index, and a snippet with the matched term highlighted.
- **Semantic search** — runs a local `all-MiniLM-L6-v2` sentence-transformers model. The document is split into sentences, each sentence and the query are embedded, and results are ranked by cosine similarity. No external API required.

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
  -d '{"title": "My Document", "content": "Hello this is my first document."}'
```

**Response `201`**
```json
{
  "id": 1,
  "title": "My Document",
  "content": "Hello this is my first document.",
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
  "content": "Hello this is my first document.",
  "version": 1,
  "created_at": "2026-03-20T10:00:00+00:00",
  "updated_at": "2026-03-20T10:00:00+00:00"
}
```

---

### Replace Text

**`PATCH /api/documents/<id>/replace-text/`**

Replaces a search term in the document content and logs the change. Use `occurrence` (0-based) to target a specific instance — omit it to replace all occurrences.

| Field | Type | Required |
|---|---|---|
| `search` | string | Yes |
| `replacement` | string | Yes |
| `occurrence` | integer | No — omit to replace all |

```bash
curl -X PATCH http://127.0.0.1:8000/api/documents/1/replace-text/ \
  -H "Content-Type: application/json" \
  -d '{"search": "Hello", "replacement": "Hi", "occurrence": 0}'
```

**Response `200`**
```json
{
  "id": 1,
  "title": "My Document",
  "content": "Hi this is my first document.",
  "version": 2,
  "created_at": "2026-03-20T10:00:00+00:00",
  "updated_at": "2026-03-20T10:05:00+00:00"
}
```

**Response `404`** — search term not found
```json
{
  "error": "\"Hello\" not found in document"
}
```

**Response `400`** — occurrence out of range
```json
{
  "error": "Occurrence 5 does not exist (found 1)"
}
```

---

### Search Within a Document

**`GET /api/documents/<id>/search/?q=<query>`**

Returns all matches with their position, occurrence index, match text, and a snippet with the matched term wrapped in `>>>` and `<<<`.

```bash
curl "http://127.0.0.1:8000/api/documents/1/search/?q=first"
```

**Response `200`**
```json
{
  "id": 1,
  "query": "first",
  "total": 1,
  "matches": [
    {
      "occurrence": 0,
      "position": 18,
      "match_text": "first",
      "snippet": "Hi this is my >>>first<<< document."
    }
  ]
}
```

**Response `404`** — query not found
```json
{
  "error": "\"first\" not found in document"
}
```

---

### Search Across All Documents

**`GET /api/documents/search/?q=<query>`**

Returns all documents containing the query as a substring. Each document includes all matches with position and snippet.

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
      "title": "My Document",
      "matches": [
        {"occurrence": 0, "position": 22, "snippet": "Hello this is my first >>>document<<<."},
        {"occurrence": 1, "position": 55, "snippet": "Hello this is my second >>>document<<<."}
      ]
    }
  ]
}
```

---

### Semantic Search Within a Document

**`GET /api/documents/<id>/semantic-search/?q=<query>`**

Finds the most relevant sentences in a document by meaning, not exact keywords. Returns up to 5 results ranked by similarity score (0–1).

```bash
curl "http://127.0.0.1:8000/api/documents/1/semantic-search/?q=introduction"
```

**Response `200`**
```json
{
  "id": 1,
  "query": "introduction",
  "results": [
    {
      "rank": 1,
      "score": 0.7431,
      "text": "Hello this is my first document."
    },
    {
      "rank": 2,
      "score": 0.3012,
      "text": "Hello this is my second document."
    }
  ]
}
```

---

### List Tracked Changes

**`GET /api/documents/<id>/changes/`**

Returns all pending change records for a document.

```bash
curl http://127.0.0.1:8000/api/documents/1/changes/
```

**Response `200`**
```json
{
  "id": 1,
  "version": 2,
  "changes": [
    {
      "id": 1,
      "original_text": "Hello",
      "replacement_text": "Hi",
      "position": 0,
      "version_at_change": 1,
      "created_at": "2026-03-20T10:05:00+00:00"
    }
  ]
}
```

---

### Accept a Change

**`POST /api/documents/<id>/changes/<change_id>/accept/`**

Marks a change as accepted and removes it from the change log. The replacement is already applied to the document content so no content change happens here.

```bash
curl -X POST http://127.0.0.1:8000/api/documents/1/changes/1/accept/
```

**Response `200`**
```json
{
  "status": "accepted",
  "change_id": 1
}
```

---

### Reject a Change

**`POST /api/documents/<id>/changes/<change_id>/reject/`**

Reverts the replacement back to the original text and removes the change record. Version increments.

```bash
curl -X POST http://127.0.0.1:8000/api/documents/1/changes/1/reject/
```

**Response `200`**
```json
{
  "status": "rejected",
  "change_id": 1,
  "content": "Hello this is my first document.",
  "version": 3
}
```

---

## Running Tests

```bash
python manage.py test documents.tests
```

There are 43 tests covering document creation, retrieval, text replacement, search, and semantic search.
