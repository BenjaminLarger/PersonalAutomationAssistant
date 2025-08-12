from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from agents.email_processor import EmailProcessor
from agents.calendar_manager import CalendarManager

load_dotenv()

app = FastAPI(title="Personal Automation Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

email_processor = EmailProcessor()
calendar_manager = CalendarManager()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProcessMeetingsRequest(BaseModel):
    user_id: str = "default"

@app.get("/")
async def root():
    return FileResponse('templates/index.html')

@app.get("/api")
async def api_status():
    return {"message": "Personal Automation Assistant API", "status": "running"}

@app.post("/process-meetings")
async def process_meetings(request: ProcessMeetingsRequest):
    try:
        meetings = await email_processor.get_meeting_emails(request.user_id)
        
        if not meetings:
            return {"message": "No meeting emails found", "meetings_processed": 0}
        
        processed_meetings = []
        for meeting in meetings:
            parsed_meeting = await email_processor.parse_meeting_details(meeting)
            calendar_event = await calendar_manager.create_event(parsed_meeting)
            processed_meetings.append({
                "subject": parsed_meeting.get("subject"),
                "date": parsed_meeting.get("date"),
                "time": parsed_meeting.get("time"),
                "calendar_event_id": calendar_event.get("id")
            })
        
        return {
            "message": f"Successfully processed {len(processed_meetings)} meetings",
            "meetings_processed": len(processed_meetings),
            "meetings": processed_meetings
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test-connections")
async def test_connections():
    try:
        calendar_test = calendar_manager.test_connection()
        return {
            "calendar": calendar_test,
            "gmail": {"status": "requires_auth", "message": "Gmail auth happens during first email fetch"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)