import base64
import email
from typing import List, Dict, Any
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from auth.gmail_auth import GmailAuth

class EmailProcessor:
    def __init__(self):
        self.gmail_auth = GmailAuth()
        self.llm = OpenAI(
            model_name="gpt-3.5-turbo-instruct",
            temperature=0,
            max_tokens=500
        )
        
        self.meeting_extraction_prompt = PromptTemplate(
            input_variables=["email_content"],
            template="""
            Extract meeting information from the following email content. Return a JSON object with these fields:
            - subject: The meeting title/subject
            - date: The meeting date (YYYY-MM-DD format)
            - time: The meeting time (HH:MM format, 24-hour)
            - duration: Duration in minutes (default 60 if not specified)
            - location: Meeting location or "Online" if virtual
            - attendees: List of email addresses
            - meeting_link: Any video conference link (Zoom, Meet, Teams, etc.)
            - description: Brief description or agenda
            
            Email content:
            {email_content}
            
            JSON:
            """
        )
    
    async def get_meeting_emails(self, user_id: str = "default") -> List[Dict[str, Any]]:
        try:
            service = self.gmail_auth.get_service()
            
            # Search for emails with 'meetings' label
            query = "label:meetings"
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            email_data = []
            for message in messages[:10]:  # Limit to 10 recent emails
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                
                # Extract email content
                payload = msg['payload']
                headers = payload.get('headers', [])
                
                subject = ""
                sender = ""
                date = ""
                
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                    elif header['name'] == 'From':
                        sender = header['value']
                    elif header['name'] == 'Date':
                        date = header['value']
                
                # Get email body
                body = self._extract_body(payload)
                
                email_data.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body
                })
            
            return email_data
            
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
    
    def _extract_body(self, payload):
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    async def parse_meeting_details(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            email_content = f"""
            Subject: {email_data['subject']}
            From: {email_data['sender']}
            Date: {email_data['date']}
            Body: {email_data['body']}
            """
            
            prompt = self.meeting_extraction_prompt.format(email_content=email_content)
            response = self.llm(prompt)
            
            # Parse the JSON response
            import json
            try:
                meeting_details = json.loads(response.strip())
                meeting_details['email_id'] = email_data['id']
                return meeting_details
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return {
                    'subject': email_data['subject'],
                    'date': '2024-01-01',
                    'time': '09:00',
                    'duration': 60,
                    'location': 'TBD',
                    'attendees': [email_data['sender']],
                    'meeting_link': '',
                    'description': email_data['body'][:200],
                    'email_id': email_data['id']
                }
                
        except Exception as e:
            print(f"Error parsing meeting details: {str(e)}")
            return {
                'subject': email_data.get('subject', 'Unknown Meeting'),
                'date': '2024-01-01',
                'time': '09:00',
                'duration': 60,
                'location': 'TBD',
                'attendees': [],
                'meeting_link': '',
                'description': 'Error parsing meeting details',
                'email_id': email_data.get('id', '')
            }