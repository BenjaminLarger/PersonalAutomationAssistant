import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import caldav
from icalendar import Calendar, Event as ICalEvent
from caldav.lib.error import AuthorizationError

class CalendarManager:
    def __init__(self):
        self.calendar_url = None
        self.username = None
        self.password = None
        self.calendar = None
        self._setup_calendar()
    
    def _setup_calendar(self):
        # For Apple Calendar, users would typically use iCloud CalDAV
        # URL format: https://caldav.icloud.com/[user_id]/calendars/
        # This is a simplified implementation - in production, you'd want proper OAuth
        self.calendar_url = os.getenv('CALDAV_URL', 'https://caldav.icloud.com/')
        self.username = os.getenv('CALDAV_USERNAME', '')
        self.password = os.getenv('CALDAV_PASSWORD', '')
        
        if self.calendar_url and self.username and self.password:
            try:
                client = caldav.DAVClient(
                    url=self.calendar_url,
                    username=self.username,
                    password=self.password
                )
                principal = client.principal()
                calendars = principal.calendars()
                if calendars:
                    self.calendar = calendars[0]  # Use first available calendar
            except Exception as e:
                print(f"Warning: Could not connect to CalDAV server: {e}")
                self.calendar = None
    
    async def create_event(self, meeting_details: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not self.calendar:
                # Fallback: save to local file or mock response
                return await self._create_mock_event(meeting_details)
            
            # Create iCalendar event
            cal = Calendar()
            cal.add('prodid', '-//Personal Automation Assistant//EN')
            cal.add('version', '2.0')
            
            event = ICalEvent()
            event.add('summary', meeting_details.get('subject', 'Meeting'))
            event.add('description', meeting_details.get('description', ''))
            
            # Parse date and time
            meeting_date = meeting_details.get('date', '2024-01-01')
            meeting_time = meeting_details.get('time', '09:00')
            duration = meeting_details.get('duration', 60)
            
            # Create datetime objects
            start_datetime = datetime.strptime(f"{meeting_date} {meeting_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)
            
            event.add('dtstart', start_datetime)
            event.add('dtend', end_datetime)
            event.add('location', meeting_details.get('location', ''))
            
            # Add attendees
            for attendee in meeting_details.get('attendees', []):
                event.add('attendee', f'mailto:{attendee}')
            
            # Add meeting link to description if available
            if meeting_details.get('meeting_link'):
                description = meeting_details.get('description', '')
                description += f"\n\nMeeting Link: {meeting_details['meeting_link']}"
                event['description'] = description
            
            event.add('uid', f"meeting-{meeting_details.get('email_id', 'unknown')}")
            event.add('dtstamp', datetime.utcnow())
            
            cal.add_component(event)
            
            # Save to CalDAV server
            self.calendar.save_event(cal.to_ical().decode('utf-8'))
            
            return {
                'id': event['uid'],
                'status': 'created',
                'calendar': 'Apple Calendar',
                'start_time': start_datetime.isoformat(),
                'end_time': end_datetime.isoformat()
            }
            
        except Exception as e:
            print(f"Error creating calendar event: {str(e)}")
            return await self._create_mock_event(meeting_details)
    
    async def _create_mock_event(self, meeting_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback method when CalDAV is not available.
        In production, this could save to a local calendar file or queue for later sync.
        """
        event_id = f"mock-event-{meeting_details.get('email_id', 'unknown')}"
        
        # Save to local file for demonstration
        events_file = "local_events.txt"
        with open(events_file, "a") as f:
            f.write(f"\n--- Event Created ---\n")
            f.write(f"ID: {event_id}\n")
            f.write(f"Subject: {meeting_details.get('subject', 'Meeting')}\n")
            f.write(f"Date: {meeting_details.get('date', '2024-01-01')}\n")
            f.write(f"Time: {meeting_details.get('time', '09:00')}\n")
            f.write(f"Duration: {meeting_details.get('duration', 60)} minutes\n")
            f.write(f"Location: {meeting_details.get('location', 'TBD')}\n")
            f.write(f"Attendees: {', '.join(meeting_details.get('attendees', []))}\n")
            f.write(f"Meeting Link: {meeting_details.get('meeting_link', 'N/A')}\n")
            f.write(f"Description: {meeting_details.get('description', 'N/A')}\n")
            f.write(f"Created: {datetime.now().isoformat()}\n\n")
        
        return {
            'id': event_id,
            'status': 'created_locally',
            'calendar': 'Local File (Mock)',
            'file': events_file,
            'start_time': f"{meeting_details.get('date', '2024-01-01')}T{meeting_details.get('time', '09:00')}:00",
            'note': 'Event saved locally. Configure CalDAV credentials to sync with Apple Calendar.'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the CalDAV connection"""
        if not self.calendar:
            return {
                'connected': False,
                'message': 'CalDAV not configured. Using local storage fallback.',
                'setup_instructions': [
                    '1. Set CALDAV_URL environment variable (e.g., https://caldav.icloud.com/your_user_id/calendars/)',
                    '2. Set CALDAV_USERNAME environment variable (your Apple ID)',
                    '3. Set CALDAV_PASSWORD environment variable (app-specific password for iCloud)'
                ]
            }
        
        try:
            calendars = self.calendar.principal().calendars()
            return {
                'connected': True,
                'calendar_count': len(calendars),
                'active_calendar': str(self.calendar)
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'message': 'Connection test failed'
            }