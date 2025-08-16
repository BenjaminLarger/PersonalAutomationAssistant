import base64
import re
from typing import List, Dict, Any
from langchain_openai import OpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import PromptTemplate as CorePromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from auth.gmail_auth import GmailAuth
from fastapi import Request, HTTPException

class ParseMeetingEmail(BaseModel):
    has_meeting: bool = Field(description="Indicates if the email has set a meeting (the return is false if any of date, time or link is missing)")
    sender: str = Field(description="The sender of the email")
    date: str = Field(description="The date of the meeting using format: DD/MM/YYYY. e.g. 13/08/2025")
    start_time: str = Field(description="The start time of the meeting using european format: HH:MM. e.g, 16:30")
    end_time: str = Field(description="The end time of the meeting using european format: HH:MM. e.g, 17:00")
    body: str = Field(description="The body of the email")
    meeting_link: str = Field(description="The video conference link for the meeting")

class LangchainMeetingEmailParser:
    def __init__(self):
        self.model = ChatOpenAI(temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=ParseMeetingEmail)
        self.prompt = CorePromptTemplate(
            template="""
            You are a meeting email parser.
            Help me extract the meeting email details.\n{format_instructions}\n{query}\n
            If you do not know the answer, please say UNKNOWN.
            """,
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.chain = self.prompt | self.model | self.parser
    
    def parse_meeting_email(self, email_content: str) -> Dict[str, Any]:
        """Parse meeting email content and return structured data"""
        try:
            output = self.chain.invoke({"query": email_content})
            print(f"Parsed output: {output}")
            return {
                'has_meeting': output.has_meeting,
                'sender': output.sender,
                'date': output.date,
                'start_time': output.start_time,
                'end_time': output.end_time,
                'body': output.body
            }
        except Exception as e:
            print(f"Error parsing meeting email with Langchain: {str(e)}")
            return {
                'has_meeting': False,
                'sender': 'UNKNOWN',
                'date': 'UNKNOWN',
                'start_time': 'UNKNOWN',
                'end_time': 'UNKNOWN',
                'body': email_content[:200] if email_content else 'UNKNOWN'
            }

class EmailProcessor:
    def __init__(self):
        self.gmail_auth = GmailAuth()
        self.langchain_parser = LangchainMeetingEmailParser()
        # Keep legacy LLM for fallback if needed
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
            
            # Group content by subject
            grouped_content = self._group_by_subject(all_content)
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
            print(f"Extracting meeting info from email: {email_data}")
            email_content = f"""
            Subject: {email_data['subject']}
            From: {email_data['sender']}
            Date: {email_data['date']}
            Body: {email_data['body']}
            """
            # print(f"Extracting meeting info from email: {email_data['subject']}")
            
            # Use the new LangchainMeetingEmailParser
            parsed_result = self.langchain_parser.parse_meeting_email(email_content)

            # Check if the email has a meeting
            if parsed_result['has_meeting'] is False:
                return None
            
            # Convert to the expected format with additional fields
            meeting_details = {
                'subject': email_data['subject'],
                'date': parsed_result.get('date', '2025-01-01'),
                'start_time': parsed_result.get('start_time', '09:00'),
                'end_time': parsed_result.get('end_time', '10:00'),
                'duration': self._calculate_duration(parsed_result.get('start_time', '09:00'), 
                                                   parsed_result.get('end_time', '10:00')),
                'location': 'TBD',
                'attendees': [parsed_result.get('sender', email_data['sender'])],
                'meeting_link': '',
                'description': parsed_result.get('body', email_data['body'])[:200],
                'email_id': email_data['id'],
                'has_meeting': parsed_result.get('has_meeting', True)
            }
            
            print(f"Parsed meeting details with Langchain: {meeting_details}")
            return meeting_details
                
        except Exception as e:
            print(f"Error parsing meeting details: {str(e)}")
            raise Exception(f"Failed to extract meeting info: {str(e)}")
    
    def _calculate_duration(self, start_time: str, end_time: str) -> int:
        """Calculate duration in minutes between start and end time"""
        try:
            if start_time == 'UNKNOWN' or end_time == 'UNKNOWN':
                return 60
            
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            
            duration = end_minutes - start_minutes
            return duration if duration > 0 else 60
        except:
            return 60
    
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
        
        # Remove common email prefixes (case insensitive)
        prefixes = [r'^re:\s*', r'^fwd?:\s*', r'^fw:\s*', r'^reply:\s*', r'^forward:\s*']
        
        normalized = subject
        for prefix in prefixes:
            normalized = re.sub(prefix, '', normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace and normalize
        normalized = ' '.join(normalized.split())
        
        return normalized if normalized else 'No Subject'