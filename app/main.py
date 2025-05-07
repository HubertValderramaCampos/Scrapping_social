from fastapi import FastAPI
from app.api.agents.api import api_router

app = FastAPI(title="TikTok Scraper API")

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)