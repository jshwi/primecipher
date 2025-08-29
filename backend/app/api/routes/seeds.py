from fastapi import APIRouter, Depends
from ...deps.auth import require_refresh_token
from ...seeds import get_seeds, reload_seeds
from ...schemas import SeedsV2

router = APIRouter()

@router.get("/seeds", response_model=SeedsV2)
def api_get_seeds() -> SeedsV2:
    return get_seeds()

@router.post("/seeds/reload", response_model=SeedsV2)
def api_reload_seeds(_=Depends(require_refresh_token)) -> SeedsV2:
    return reload_seeds()
