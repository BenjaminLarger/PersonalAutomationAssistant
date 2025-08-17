import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from api import auth
from starlette.middleware.sessions import SessionMiddleware
from services.email_processor import EmailProcessor
from services.calendar_manager import CalendarManager
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

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


@app.post("/api/create-calendar-events")
async def create_calendar_events_endpoint(request: Request):
    """
    Process meetings and create calendar events from them
    """
    access_token = request.session.get('access_token')
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email_processor = EmailProcessor()
    
    try:
        # Get and process all meetings
        grouped_meetings = await email_processor.get_all_meetings_content(request)
        if not grouped_meetings:
            return {"success": True, "message": "No meetings found", "events_created": 0}
        
        # Create calendar service using Gmail credentials (extended scope needed)
        # Note: This would require calendar scope in the OAuth flow
        calendar_creds = Credentials(
            token=access_token,
            refresh_token=request.session.get('refresh_token'),
            token_uri=request.session.get('token_uri'),
            client_id=request.session.get('client_id'),
            client_secret=request.session.get('client_secret'),
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        calendar_service = build('calendar', 'v3', credentials=calendar_creds)
        calendar_manager = CalendarManager(calendar_service)
        
        # Process each email group and create calendar events
        events_created = 0
        created_events = []
        
        for subject, emails in grouped_meetings.items():
            for email_data in emails:
                try:
                    meeting_info = await email_processor.extract_meeting_info(email_data)
                    if meeting_info and meeting_info.get('has_meeting', False):
                        # Create calendar event
                        calendar_manager.add_event(meeting_info)
                        events_created += 1
                        created_events.append({
                            'subject': meeting_info.get('subject'),
                            'date': meeting_info.get('date'),
                            'start_time': meeting_info.get('start_time'),
                            'end_time': meeting_info.get('end_time')
                        })
                except Exception as e:
                    print(f"Error creating calendar event for {email_data.get('subject', 'Unknown')}: {str(e)}")
                    continue
        
        return {
            "success": True,
            "events_created": events_created,
            "created_events": created_events,
            "message": f"Successfully created {events_created} calendar events"
        }
        
    except Exception as e:
        print(f"Error creating calendar events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create calendar events: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
