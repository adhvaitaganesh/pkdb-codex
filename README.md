# PKDB Codex (Draft)

This repository contains a first-draft FastAPI backend for the pharmacological data management platform described in the specification. It focuses on role-based access, dataset metadata, and access requests.

## Features (Draft)
- Email/password registration and token-based authentication
- Role-aware dataset creation and editing
- Lock/unlock dataset controls (admin only)
- Access requests for locked datasets

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API docs.

## MongoDB configuration
Set `PKDB_USE_MONGO=true` along with `PKDB_MONGO_URI` and `PKDB_MONGO_DB` to use MongoDB-backed storage.

```bash
export PKDB_USE_MONGO=true
export PKDB_MONGO_URI="mongodb://localhost:27017"
export PKDB_MONGO_DB="pkdb"
```

## Example workflow
1. Register a user:
   ```bash
   curl -X POST http://127.0.0.1:8000/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"email":"alice@example.com","password":"secret","role":"researcher"}'
   ```
2. Exchange credentials for a token:
   ```bash
   curl -X POST http://127.0.0.1:8000/auth/token \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=alice@example.com&password=secret'
   ```
3. Use the token to create a dataset.

## Notes
- The current storage layer uses an in-memory store by default. Swap to MongoDB by implementing the `Storage` protocol in `app/storage.py` or enabling `PKDB_USE_MONGO`.
- Change `PKDB_JWT_SECRET` in your environment before deploying.
