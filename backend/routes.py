from fastapi import APIRouter
from backend import endpoints



# Create a router to expose the endpoints.
router = APIRouter()
router.include_router(endpoints.router)