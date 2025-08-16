import base64
import email
from typing import List, Dict, Any
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from auth.gmail_auth import GmailAuth
from fastapi import Request, HTTPException

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
    
    async def get_all_meetings_content(self, request: Request) -> Dict[str, List[Dict[str, Any]]]:
        try:
            service = await self.gmail_auth.get_service(request)
            if not service:
                raise Exception("Failed to get Gmail service")
            
            # Get all content from emails with 'meetings' label
            query = "label:meetings"
            results = service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            all_content = []
            print(f"Found {len(messages)} messages")
            for message in messages:  # Process all messages, not just 10
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

                print(f"Processing email: {subject} from {sender} on {date}")
                
                all_content.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body
                })
            print(f"all_content: {all_content}")
            
            # Group content by subject
            grouped_content = self._group_by_subject(all_content)
            print(f"grouped_content: {grouped_content}")
            return grouped_content
            
        except HTTPException:
            # Re-raise authentication errors
            raise
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return {}
    
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
    
    async def extract_meeting_info(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _group_by_subject(self, all_content: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group emails by subject, handling common email thread patterns like 'Re:', 'Fwd:', etc.
        Returns a dictionary where keys are normalized subjects and values are lists of emails.
        """
        grouped = {}
        
        for email in all_content:
            subject = email.get('subject', 'No Subject').strip()
            
            # Normalize subject by removing common prefixes
            normalized_subject = self._normalize_subject(subject)
            
            if normalized_subject not in grouped:
                grouped[normalized_subject] = []
            
            grouped[normalized_subject].append(email)
        
        # Sort groups by the most recent email date in each group
        for subject in grouped:
            grouped[subject].sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return grouped
    
    def _normalize_subject(self, subject: str) -> str:
        """
        Normalize email subject by removing common prefixes and extra whitespace.
        """
        import re
        
        # Remove common email prefixes (case insensitive)
        prefixes = [r'^re:\s*', r'^fwd?:\s*', r'^fw:\s*', r'^reply:\s*', r'^forward:\s*']
        
        normalized = subject
        for prefix in prefixes:
            normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace and normalize
        normalized = ' '.join(normalized.split())
        
        return normalized if normalized else 'No Subject'