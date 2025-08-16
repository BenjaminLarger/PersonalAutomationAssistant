import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from api import auth
from starlette.middleware.sessions import SessionMiddleware

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
    
    from agents.email_processor import EmailProcessor
    email_processor = EmailProcessor()
    
    meetings_content = await email_processor.get_all_meetings_content(request)
    if meetings_content is None:
        raise HTTPException(status_code=500, detail="Failed to fetch meetings content")
    
    return {"success": True, "meetings_content": meetings_content, "count": len(meetings_content)}

@app.post("/api/process-all-meetings")
async def process_all_meetings_endpoint(request: Request):
    """
    Process all meetings content from Gmail 'meetings' label and extract meeting information
    """
    access_token = request.session.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from agents.email_processor import EmailProcessor
    email_processor = EmailProcessor()
    
    # Get all meetings content
    meetings_content = await email_processor.get_all_meetings_content(request)
    if not meetings_content:
        return {"success": True, "processed_meetings": [], "message": "No meetings found"}
    
    # Process each email to extract meeting information
    processed_meetings = []
    for email_data in meetings_content:
        meeting_info = await email_processor.extract_meeting_info(email_data)
        processed_meetings.append(meeting_info)
    
    return {
        "success": True, 
        "processed_meetings": processed_meetings, 
        "total_count": len(processed_meetings)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
