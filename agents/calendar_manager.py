import os
from datetime import datetime
from typing import Dict, Any
from googleapiclient.errors import HttpError

class CalendarManager:
    def __init__(self, service):
        self.service = service

    def add_event(self, meeting_details: Dict[str, Any]) -> None:
      try:
        # Call the Calendar API
        now = datetime.today().strftime('%Y-%m-%d')
        date = meeting_details.get('date', now)
        # Convert date from DD/MM/YYYY to YYYY-MM-DD
        try:
            date = datetime.strptime(date, "%d/%m/%Y").strftime('%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format: {date}. Using current date instead.")
            date = now
        start_time = meeting_details.get('start_time', '09:00')
        end_time = meeting_details.get('end_time', '10:00')
        # Ensure time format is HH:MM, then add seconds
        if len(start_time.split(':')) == 2:  # HH:MM format
            start_date_time = f"{date}T{start_time}:00+01:00"
        else:  # Already includes seconds
            start_date_time = f"{date}T{start_time}+01:00"
        
        if len(end_time.split(':')) == 2:  # HH:MM format
            end_date_time = f"{date}T{end_time}:00+01:00"
        else:  # Already includes seconds
            end_date_time = f"{date}T{end_time}+01:00"
        event = {
          'summary': meeting_details.get('subject', 'No Title'),
          'location': meeting_details.get('location', 'Online'),
          'description': meeting_details.get('description', 'No Description'),
          'start': {
            'dateTime': start_date_time,
            'timeZone': 'Europe/Paris',
          },
          'end': {
            'dateTime': end_date_time,
            'timeZone': 'Europe/Paris',
          },
          'recurrence': [],
          'attendees': [],
          'reminders': {
            'useDefault': False,
            'overrides':
            [
              {'method': 'email', 'minutes': 2 * 60},
              {'method': 'popup', 'minutes': 10},
            ],
          },
        }
        print(f"Adding event: {event}")

        event = self.service.events().insert(calendarId='primary', body=event).execute()
        print(f'Event created: {event.get("htmlLink")}')
      except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
  from google_auth_oauthlib.flow import InstalledAppFlow
  from google.oauth2.credentials import Credentials
  from google.auth.transport.requests import Request
  from googleapiclient.discovery import build

  SCOPES = ["https://www.googleapis.com/auth/calendar"]

  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "client_secret.json", SCOPES
      )
      creds = flow.run_local_server(host="127.0.0.1", port=8080)

  try:
    service = build("calendar", "v3", credentials=creds)
    a = CalendarManager(service=service)
    a.add_event({
      'subject': 'Test Event',
      'location': 'Online',
      'description': 'This is a test event',
      'date': '06/01/2025',
      'start_time': '10:00:00',
      'end_time': '11:00:00',
    })
  except Exception as e:
    print(f"An error occurred: {e}")