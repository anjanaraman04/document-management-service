# Part II — Taking Document App to Production

This document covers what I would change and add to make this prototype ready for real users.

---

## 1. Infrastructure and Deployment

**Containerization**
- Package the app with Docker so it runs the same way on every machine

**CI/CD Pipeline**
- Set up automated testing on every push so broken code doesn't make it to production
- Separate environments for development, staging, and production

---

## 2. Authentication and Authorization

**User Authentication**
- Add user accounts with securely hashed passwords stored in the database
- Use token-based authentication so users can log in and make authorized requests
- Could also support signing in with Google or GitHub to make onboarding easier

**Roles and Permissions**
- Give users different roles like `admin`, `editor`, and `viewer`
- Only editors and admins should be able to create or update documents

**Basic Security**
- Protect all endpoints so only logged-in users can access them
- Add CORS and CSRF protections

---

## 3. Database

**Relational Database (PostgreSQL)**
- Replace SQLite with PostgreSQL for all structured data: user accounts, roles, permissions, document metadata (ownership, timestamps, versions)
- Enforce constraints at the database level

**Document Storage (NoSQL)**
- Move document content to a NoSQL store (MongoDB or DynamoDB) for:
  - Flexible schema to accommodate varying document structures
  - Fast read/write performance
  - Horizontal scalability for large document datasets

**Versioning**
- Right now the app logs each individual text replacement as a `DocumentChange` record, which tracks what changed, where, and at what version
- The next step would be saving a full content snapshot before every edit so users can browse history and restore any previous version — kind of like Git commits for documents
- This would also make the accept/reject workflow more reliable since you'd always have a clean copy to fall back on

---

## 4. Scalability and Performance

**Scaling the App**
- Run multiple instances of the app behind a load balancer to handle more traffic
- Enable auto-scaling based on traffic metrics

**Database Scaling**
- Use read replicas for read-heavy workloads (search, document retrieval)
- Separate read and write paths where appropriate

**Caching**
- Cache frequently accessed documents so we're not hitting the database every time
- Cache recent search results
- Clear the cache when a document is updated
- For semantic search specifically, cache the sentence embeddings for each document — right now the app re-embeds the entire document on every query, which is slow and wasteful. Embeddings only need to be recomputed when the document content actually changes

**Background Jobs**
- Move slow operations to background workers so they don't block API responses
- The biggest example right now is semantic search — the AI model (~80MB) loads into memory on the first request and re-runs embedding on every search. In production this should happen in the background, not during the request itself
- Other candidates: search indexing, generating snapshots after large edits

**Search at Scale**
- The cross-document search currently does a full scan of every document in the database (`LIKE` query), which will get slow as the number of documents grows
- A proper search index (like Elasticsearch or PostgreSQL full-text search) would make this much faster
- For semantic search, the right approach at scale is to pre-compute and store document embeddings in a vector database (like FAISS or pgvector), then query against that index instead of re-embedding everything on every request

**API Improvements**
- Add pagination so large lists don't return everything at once
- Optimize slow database queries

---

## 5. New Features Added Since v1

**Find & Replace (Redlining)**
- The app now works like Microsoft Word's Track Changes — users can find specific occurrences of text, replace them, and every change is logged
- In production, a key concern would be concurrent editing: if two users are editing the same document at the same time, changes could overwrite each other. This would need optimistic locking or real-time conflict detection

**Semantic Search**
- Added a semantic search feature powered by a local AI model (`all-MiniLM-L6-v2` from sentence-transformers)
- Instead of matching exact keywords, it understands the meaning of a query and finds the most relevant sentences in a document
- Currently runs entirely on the server with no GPU — fine for a prototype but would need proper infrastructure (background workers, embedding cache, vector store) before going to production

**Cross-Document Search with Jump to Edit**
- Users can search across all documents and jump directly into the Find & Replace editor with the search term pre-filled
- This connects the search and editing workflows, which makes it more useful than having them as separate features

---

## 6. Monitoring

**Logging**
- Log important events like API requests, errors, and failed login attempts
- Centralised structured logging in JSON format

**Metrics**
- Track: request latency (p50, p95, p99), error rates, throughput (req/sec), and database query performance

**Alerts**
- Set up alerts for: high error rates, latency spikes, and service downtime
