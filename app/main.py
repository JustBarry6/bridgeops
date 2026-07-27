from fastapi import FastAPI

app = FastAPI(title="BridgeOps")

@app.get("/health")
def health():
    return {"status": "ok"}