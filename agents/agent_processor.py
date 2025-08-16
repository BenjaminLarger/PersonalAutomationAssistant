from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
model = ChatOpenAI(temperature=0)
from datetime import datetime

# Define your desired data structure.
class ParseMeetingEmail(BaseModel):
    has_meeting: bool = Field(description="Indicates if the email is about a meeting")
    sender: str = Field(description="The sender of the email")
    date: str = Field(description="The date of the meeting using format: DD/MM/YYYY. e.g. 13/08/2025")
    start_time: str = Field(description="The start time of the meeting using european format: HH:MM. e.g, 16:30")
    end_time: str = Field(description="The end time of the meeting using european format: HH:MM. e.g, 17:00")
    body: str = Field(description="The body of the email")

class LangchainMeetingEmailParser:
    def __init__(self, email_body: str):
        self.model = model
        self.email_body = email_body
        self.parser = PydanticOutputParser(pydantic_object=ParseMeetingEmail)
        self.prompt = PromptTemplate(
            template="""
            You are a meeting email parser.
            Help me extract the meeting email details.\n{format_instructions}\n{query}\n
            """,
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.chain = self.prompt | self.model | self.parser

    def parse(self):
        response = self.chain.invoke({"query": self.email_body})
        return response

if __name__ == "__main__":
    # Example usage
    email_body = """
    Benjamin & Helena -Ironhack IA

    Miércoles, 13 de agosto 2025 · 12:30 – 1:00pm Zona horaria: Europe/Madrid
    """
    parser = LangchainMeetingEmailParser(email_body)
    parsed_data = parser.parse()
    print(parsed_data)  # Output the parsed meeting details