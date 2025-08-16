import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from api import auth
from api.auth import get_latest_email
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()
app.include_router(auth.router, prefix="/api/authentication", tags=["auth"])
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "default_secret_key"))

templates = Jinja2Templates(directory="static/")

@app.get("/")
async def login(request: Request):
    """
    :param request: An instance of the `Request` class, representing the incoming HTTP request.
    :return: A TemplateResponse object rendering the "login.html" template with the given request context.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/welcome")
async def welcome(request: Request):
    print(f"Welcome request.url_for('auth_callback'): {request.url_for('auth_callback')}")
    user_name = request.session.get('user_name', 'User')
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "user_name": user_name
    })

@app.get("/api/latest-email")
async def get_latest_email_endpoint(request: Request):
    """
    Get the latest email from the user's Gmail account
    """
    access_token = request.session.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    latest_email = get_latest_email(access_token)
    if latest_email is None:
        raise HTTPException(status_code=500, detail="Failed to fetch latest email")
    
    # Extract relevant information from the email
    email_data = {
        "id": latest_email.get('id'),
        "snippet": latest_email.get('snippet'),
        "thread_id": latest_email.get('threadId'),
        "labels": latest_email.get('labelIds', [])
    }
    
    # Extract headers for subject, from, date
    headers = latest_email.get('payload', {}).get('headers', [])
    for header in headers:
        name = header.get('name', '').lower()
        if name == 'subject':
            email_data['subject'] = header.get('value')
        elif name == 'from':
            email_data['from'] = header.get('value')
        elif name == 'date':
            email_data['date'] = header.get('value')
    
    return {"success": True, "email": email_data}
