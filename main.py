import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from api import auth
from starlette.middleware.sessions import SessionMiddleware
from agents.email_processor import EmailProcessor

app = FastAPI(debug=True)
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

@app.get("/api/meetings-content")
async def get_all_meetings_content_endpoint(request: Request):
    """
    Get all content from emails labeled 'meetings' in the user's Gmail account
    """
    access_token = request.session.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email_processor = EmailProcessor()
    
    grouped_meetings = await email_processor.get_all_meetings_content(request)
    if grouped_meetings is None:
        raise HTTPException(status_code=500, detail="Failed to fetch meetings content")
    
    # Calculate total count across all groups
    total_count = sum(len(emails) for emails in grouped_meetings.values())
    
    return {
        "success": True, 
        "grouped_meetings": grouped_meetings, 
        "total_count": total_count,
        "groups_count": len(grouped_meetings)
    }

@app.get("/process-meetings")
async def process_meetings_page(request: Request):
    """
    Redirect to the process meetings functionality
    """
    access_token = request.session.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Redirect to the welcome page where the actual processing happens
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "user_name": request.session.get('user_name', 'User')
    })

@app.post("/api/process-all-meetings")
async def process_all_meetings_endpoint(request: Request):
    """
    Process all meetings content from Gmail 'meetings' label and extract meeting information
    """
    access_token = request.session.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email_processor = EmailProcessor()
    
    # Get all meetings content (now grouped by subject)
    grouped_meetings = await email_processor.get_all_meetings_content(request)
    if not grouped_meetings:
        return {"success": True, "processed_meetings": {}, "message": "No meetings found"}
    
    # Process each email group to extract meeting information
    processed_groups = {}
    for subject, emails in grouped_meetings.items():
        processed_groups[subject] = []
        for email_data in emails:
            meeting_info = await email_processor.extract_meeting_info(email_data)
            if meeting_info is not None:
              processed_groups[subject].append(meeting_info)
    
    # Calculate total count across all groups
    total_count = sum(len(meetings) for meetings in processed_groups.values())
    
    return {
        "success": True, 
        "processed_meetings": processed_groups, 
        "total_count": total_count,
        "groups_count": len(processed_groups)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
