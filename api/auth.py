import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
print("GOOGLE_CLIENT_ID:", GOOGLE_CLIENT_ID)
print("GOOGLE_CLIENT_SECRET:", GOOGLE_CLIENT_SECRET)

@router.get("/login")
async def login(request: Request):
    print(f"request.url_for('auth_callback'): {request.url_for('auth_callback')}")
    redirect_uri = request.url_for('auth_callback')
    scope = "openid email profile https://www.googleapis.com/auth/gmail.readonly"
    google_auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"

    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
async def auth_callback(code: str, request: Request):
    print(f"request.url_for('auth_callback'): {request.url_for('auth_callback')}")
    token_request_uri = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': request.url_for('auth_callback'),
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
        request.session['user_name'] = name
        request.session['access_token'] = token_response.get('access_token')
        latest_message = get_latest_email(request.session['access_token'])
        print(f"Latest email: {latest_message}")
        return RedirectResponse(url=request.url_for('welcome'))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Later, in another endpoint
def get_latest_email(access_token):
    try:
      creds = Credentials(token=access_token)
      service = build('gmail', 'v1', credentials=creds)
      
      results = service.users().messages().list(userId='me', maxResults=1).execute()
      messages = results.get('messages', [])
      
      if messages:
          message = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
          return message
    except Exception as e:
        print(f"Error fetching latest email: {e}")
        return None