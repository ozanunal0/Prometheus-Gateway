from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root() -> dict[str, str]:
    """Health check endpoint to confirm the server is running correctly."""
    return {"message": "Prometheus Gateway is running"} 