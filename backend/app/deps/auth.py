import os
from fastapi import HTTPException, Request, status

def require_refresh_token(request: Request):
    expected = os.getenv("REFRESH_TOKEN")
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer")
    token = auth.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")

import os
from fastapi import Header, HTTPException

def require_refresh_auth(authorization: str = Header(None)) -> None:
    expected = os.getenv("REFRESH_TOKEN")
    if expected:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing/invalid auth header")
        token = authorization.split(" ", 1)[1]
        if token != expected:
            raise HTTPException(status_code=401, detail="invalid refresh token")
