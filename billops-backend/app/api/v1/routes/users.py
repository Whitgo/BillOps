from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def list_users() -> dict[str, str]:
    return {"message": "list users placeholder"}
