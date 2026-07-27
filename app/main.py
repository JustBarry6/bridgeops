from fastapi import FastAPI

from app.api.transfers import router as transfers_router
from app.core.database import Base, engine
from app.models import transfer  # noqa: F401 — nécessaire pour enregistrer le modèle avant create_all

app = FastAPI(title="BridgeOps")

Base.metadata.create_all(bind=engine)

app.include_router(transfers_router)


@app.get("/health")
def health():
    return {"status": "ok"}