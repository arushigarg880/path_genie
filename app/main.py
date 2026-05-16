from fastapi import FastAPI

app = FastAPI(
    title="PathGenie API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "PathGenie backend is running"}