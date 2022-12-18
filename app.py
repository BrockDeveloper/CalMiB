from fastapi import FastAPI
from backend.routes import router



# fastapi application
app = FastAPI()
app.include_router(router)