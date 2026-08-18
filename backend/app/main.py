from fastapi import FastAPI

app = FastAPI(title="NusaGuard API")

@app.get("/health")
def health():
    return {"status": "ok"}