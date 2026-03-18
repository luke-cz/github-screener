from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def health() -> dict:
    return {"status": "ok"}
