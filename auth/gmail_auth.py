import os
from google.oauth2 import id_token
from googleapiclient.discovery import build
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, HTTPException
import httpx
from google.auth.transport import requests

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailAuth:
    def __init__(self):
        self.creds = None
        self.service = None

    async def get_service(self, request: Request):
        if not self.service:
            return await login(request)
        return self.service

@router.get("/login")
async def login(request: Request):
    print("Login route accessed")
    # Force localhost for Google OAuth compatibility
    redirect_uri = "http://localhost:8000/api/authentication/callback"
    scope = "openid email profile https://www.googleapis.com/auth/gmail.readonly"
    google_auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"

    return RedirectResponse(url=google_auth_url)

@router.get("/callback")
async def auth_callback(code: str, request: Request):
    print(f"Auth callback triggered with code: {code}")
    token_request_uri = "https://oauth2.googleapis.com/token"
    redirect_uri = "http://localhost:8000/api/authentication/callback"
    print(f"Redirect URI: {redirect_uri}")
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_request_uri, data=data)
        response.raise_for_status()
        token_response = response.json()

    id_token_value = token_response.get('id_token')
    if not id_token_value:
        raise HTTPException(status_code=400, detail="Missing id_token in response.")

    try:
        id_info = id_token.verify_oauth2_token(id_token_value, requests.Request(), GOOGLE_CLIENT_ID)

        name = id_info.get('name')
        # Store tokens (you may want to use a proper session store)
        print(f"User authenticated: {name}")
        return {"message": f"Authentication successful for {name}", "redirect": "/"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")