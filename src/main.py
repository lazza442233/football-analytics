from fastapi import FastAPI

app = FastAPI(title="Football Analytics")


@app.get("/health")
def health():
    return {"status": "ok"}
