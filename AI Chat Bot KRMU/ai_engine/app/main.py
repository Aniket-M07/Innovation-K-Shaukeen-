from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Smart Campus AI Engine", version="1.0.0")


@app.get("/health")
async def health() -> dict:
  return {"ok": True, "service": "Smart Campus AI Engine"}


app.include_router(router)