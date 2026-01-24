from fastapi import APIRouter

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/")
def list_integrations() -> dict[str, str]:
    return {"message": "list integrations placeholder"}
