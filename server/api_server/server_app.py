import argparse
from fastapi import FastAPI
import uvicorn


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/")
    async def hello():
        return {"message": "Hello World"}

    return app