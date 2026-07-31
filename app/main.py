from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.connections import router as connections_router
from app.api.transfers import router as transfers_router
from app.core.database import Base, engine
from app.models import connection, transfer, user  # noqa: F401

app = FastAPI(title="BridgeOps")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(transfers_router)
app.include_router(connections_router)


@app.get("/health")
def health():
    return {"status": "ok"}