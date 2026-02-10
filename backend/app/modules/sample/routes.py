from fastapi import APIRouter

router = APIRouter(prefix="/sample", tags=["sample"])


@router.get("/hello")
def hello():
    return {"message": "hello from sample module"}