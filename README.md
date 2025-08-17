# Personal Automation Assistant

An AI-powered automation agent that creates a multi-step workflow: Gmail → OpenAI Processing → Calendar Integration. Features an enhanced UI that highlights the complete program workflow for better user experience.

## 🔄 Workflow Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │    │                 │
│   📧 Gmail      │───▶│  🤖 OpenAI      │───▶│  📅 Google      │───▶│  ✅ Results     │
│   Email Fetch   │    │  AI Processing  │    │  Calendar       │    │  Display        │
│                 │    │                 │    │  Integration    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │                       │
        ▼                       ▼                       ▼                       ▼
  • OAuth Login          • LangChain           • Calendar API        • Web UI Results
  • Fetch "meetings"     • Extract Details     • Create Events       • Success/Error
  • Label Filter         • JSON Parsing        • Event Scheduling    • Event Summary
```

### Process Steps:
1. **Gmail Authentication** - OAuth 2.0 login and fetch emails labeled "meetings"
2. **AI Analysis** - LangChain + OpenAI extract structured meeting data (title, date, time, location)
3. **Calendar Creation** - Google Calendar API creates calendar events automatically
4. **Results Display** - Web interface shows processing results and created events

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   python setup.py
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Configure API Keys**
   - Copy `.env.example` to `.env`
   - Add your API keys and credentials

3. **Run the Application**
   ```bash
   python main.py
   ```

4. **Access the UI**
   - Open http://localhost:8000 in your browser

## 📋 Features

### MVP (Milestone 1)
- ✅ Gmail OAuth integration for reading emails with "meetings" label
- ✅ OpenAI integration for extracting meeting details
- ✅ Google Calendar integration via Google Calendar API
- ✅ Simple web UI for triggering automation
- ✅ FastAPI backend with LangChain integration

### Milestone 2 (Planned)
- 🔄 Multi-step planning and execution
- 🧠 Memory capabilities for context retention
- 📊 Enhanced prompt chaining

### Milestone 3 (Planned)
- 🔐 Comprehensive authentication
- 🛡️ User safety checks
- 🔒 Secure credential management

## 🔧 Setup Instructions

### 1. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add your credentials to `.env` file

### 2. Google Calendar Setup
1. In Google Cloud Console, enable the Google Calendar API
2. Use the same OAuth credentials from Gmail setup
3. Ensure your OAuth scope includes Calendar access
4. Calendar events will be created in your default Google Calendar

### 3. OpenAI Setup
1. Get an API key from OpenAI
2. Add it to your `.env` file

## 📂 Project Structure

```
PersonalAutomationAssistant/
├── agents/
│   ├── email_processor.py    # Gmail integration & AI parsing
│   └── calendar_manager.py   # Google Calendar integration
├── auth/
│   └── gmail_auth.py         # Gmail OAuth handling
├── static/
│   ├── style.css            # UI styling
│   └── script.js            # Frontend logic
├── templates/
│   └── index.html           # Main UI template
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── setup.py               # Setup script
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_secret_key_for_sessions
# Google Calendar uses the same OAuth credentials as Gmail
# No additional calendar-specific credentials needed
```

## 🎯 Usage

1. **Prepare Gmail**
   - Label meeting invitation emails with "meetings" in Gmail
   
2. **Run Automation**
   - Access the web UI at http://localhost:8000
   - Click "Process Meeting Emails"
   - The system will:
     - Fetch emails with "meetings" label
     - Extract meeting details using OpenAI
     - Create calendar events in Google Calendar

3. **View Results**
   - Check your Google Calendar for new events
   - View processing results in the web UI

## 🧠 AI Integration

### LangChain Components
- **LLM**: OpenAI GPT-3.5-turbo-instruct for meeting detail extraction
- **Prompt Templates**: Structured prompts for consistent parsing
- **Error Handling**: Fallback mechanisms for parsing failures

### Meeting Detail Extraction
The AI extracts:
- Meeting title/subject
- Date and time
- Duration
- Location (physical or virtual)
- Attendees
- Meeting links (Zoom, Teams, etc.)
- Description/agenda

## 🔒 Security Features

### Current (MVP)
- Environment variable management
- OAuth 2.0 for Gmail and Google Calendar access
- Unified Google authentication flow

### Planned (Milestone 3)
- User authentication and authorization
- Rate limiting and abuse prevention
- Audit logging
- Encrypted credential storage

## 🚧 Development

### Running in Development
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
- Test Gmail connection via OAuth flow
- Validate OpenAI API integration
- Test Google Calendar API integration
- End-to-end automation testing

## 📈 Future Enhancements

### Multi-Step Planning (Milestone 2)
- Chain multiple AI operations
- Context retention between operations
- Smart scheduling conflict detection
- Batch processing optimization

### Advanced Safety (Milestone 3)
- User consent for calendar modifications
- Dry-run mode for testing
- Rollback capabilities
- Privacy-preserving processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues

1. **Gmail OAuth fails**
   - Ensure Gmail API is enabled
   - Check redirect URIs in Google Console
   - Verify client credentials

2. **Calendar events not appearing**
   - Ensure Google Calendar API is enabled
   - Check OAuth scope includes calendar access
   - Test calendar connection endpoint

3. **OpenAI parsing errors**
   - Check API key validity
   - Monitor usage quotas
   - Review prompt templates

### Support
- Check the logs in the console
- Test individual components using `/test-connections`
- Review the `.env` configuration