from fastapi import FastAPI

app = FastAPI(title="GlasHaus API")

@app.get("/")
def health_check():
    return {"status": "GlasHaus backend running"}