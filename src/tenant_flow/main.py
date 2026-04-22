from fastapi import FastAPI

app = FastAPI(title="tenant-flow")


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "tenant-flow"}
