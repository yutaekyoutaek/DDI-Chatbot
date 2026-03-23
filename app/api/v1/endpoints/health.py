#서버가 살아 있는지 확인하는 용도
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "DDI Chatbot API is running"
    }