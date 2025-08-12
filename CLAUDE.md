# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is an AI-powered automation agent that creates a multi-step workflow: Gmail → OpenAI Processing → Calendar Integration. The architecture follows a modular agent-based design:

### Core Components

- **FastAPI Server** (`main.py`): Web API with static file serving, serves UI at localhost:8000
- **Email Agent** (`agents/email_processor.py`): Gmail OAuth integration + LangChain/OpenAI for meeting extraction  
- **Calendar Agent** (`agents/calendar_manager.py`): Apple Calendar integration via CalDAV protocol
- **Authentication** (`auth/gmail_auth.py`): Google OAuth 2.0 flow with token persistence

### Data Flow
1. UI triggers `/process-meetings` endpoint
2. `EmailProcessor` fetches emails labeled "meetings" from Gmail
3. LangChain `PromptTemplate` + OpenAI extracts structured meeting data (JSON)
4. `CalendarManager` creates CalDAV events in Apple Calendar
5. Results displayed in web interface

### Key Dependencies
- **LangChain**: Uses `langchain_openai.OpenAI` (not `langchain.llms.OpenAI`) 
- **CalDAV**: For Apple Calendar integration with fallback to local file storage
- **Google API Client**: Gmail API access with OAuth token caching in `token.pickle`

## Development Commands

### Environment Setup
```bash
python setup.py                    # Automated setup with venv creation
source venv/bin/activate           # Activate virtual environment  
python test_setup.py               # Verify configuration and dependencies
```

### Running the Application
```bash
python main.py                     # Start FastAPI server on port 8000
uvicorn main:app --reload          # Development mode with auto-reload
```

### Testing and Validation
```bash
curl http://localhost:8000/health           # API health check
curl http://localhost:8000/test-connections # Test Gmail/Calendar connections
```

## Configuration Requirements

### Environment Variables (.env)
- `OPENAI_API_KEY`: OpenAI API access for meeting parsing
- `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`: Gmail OAuth credentials
- `CALDAV_URL`/`CALDAV_USERNAME`/`CALDAV_PASSWORD`: Apple Calendar CalDAV access

### Google OAuth Setup
- Redirect URI must be configured as `http://localhost:8080` in Google Cloud Console
- Gmail API must be enabled for the project
- OAuth flow creates persistent `token.pickle` file

### Apple Calendar Integration  
- Requires app-specific password from Apple ID settings
- CalDAV URL format: `https://caldav.icloud.com/[user_id]/calendars/`
- Falls back to local file storage (`local_events.txt`) if CalDAV unavailable

## Implementation Notes

### LangChain Integration
- Uses structured `PromptTemplate` for consistent meeting data extraction
- OpenAI model: `gpt-3.5-turbo-instruct` with temperature=0 for deterministic parsing
- Fallback parsing handles malformed JSON responses

### Gmail Label Requirement
- System specifically looks for emails with "meetings" label
- Users must manually label meeting invitations in Gmail before processing

### Error Handling
- Gmail auth failures trigger OAuth re-authentication flow
- CalDAV connection issues fall back to local storage mode
- Malformed AI responses use fallback data structures

### Future Roadmap
- **Milestone 2**: Multi-step planning and memory capabilities using LangChain agents
- **Milestone 3**: Enhanced authentication, user safety checks, and secure credential management