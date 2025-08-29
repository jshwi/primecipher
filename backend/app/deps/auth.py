import os
from fastapi import HTTPException, Request, status

def require_refresh_token(request: Request):
    expected = os.getenv("REFRESH_TOKEN")
    if not expected:
        return  # auth disabled if unset
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer")
    token = auth.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
