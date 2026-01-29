from fastapi import FastAPI

from app.routers import auth, datasets, roles

app = FastAPI(title="PKDB Codex", version="0.1.0")

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(roles.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
