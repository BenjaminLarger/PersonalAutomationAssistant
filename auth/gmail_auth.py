import os
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, HTTPException
import httpx
from google.auth.transport import requests

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar'
]

class GmailAuth:
    def __init__(self):
        self.creds = None
        self.service = None

    async def get_service(self, request: Request):
        # Check if we have an access token in session
        access_token = request.session.get('access_token')
        if not access_token:
            raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
        
        # Create credentials and service if not exists or if credentials are invalid
        if not self.service or not self.creds:
            # Get all required credential components from session
            refresh_token = request.session.get('refresh_token')
            client_id = request.session.get('client_id')
            client_secret = request.session.get('client_secret')
            token_uri = request.session.get('token_uri')
            
            # Create credentials with all required fields for token refresh
            self.creds = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri=token_uri,
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
            
            # Refresh credentials if needed
            if self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(requests.Request())
                    # Update session with new access token
                    request.session['access_token'] = self.creds.token
                except Exception as e:
                    print(f"Error refreshing credentials: {str(e)}")
                    raise HTTPException(status_code=401, detail="Failed to refresh credentials. Please login again.")
            
            self.service = build('gmail', 'v1', credentials=self.creds)
        
        return self.service

@router.get("/login")
async def login(request: Request):
    print("Login route accessed")
    # Force localhost for Google OAuth compatibility
    redirect_uri = "http://localhost:8000/api/authentication/callback"
    scope = "openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar"
    google_auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent"

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
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        
        # Store all necessary tokens and credentials in session
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        request.session['user_name'] = name
        request.session['client_id'] = GOOGLE_CLIENT_ID
        request.session['client_secret'] = GOOGLE_CLIENT_SECRET
        request.session['token_uri'] = 'https://oauth2.googleapis.com/token'
        
        print(f"User authenticated: {name}")
        print(f"Refresh token available: {refresh_token is not None}")
        return RedirectResponse(url="/welcome", status_code=302)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")