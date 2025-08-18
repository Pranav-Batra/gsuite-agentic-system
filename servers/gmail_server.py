import os.path
import datetime
from mcp.server.fastmcp import FastMCP

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import base64

from dateutil import parser
import pytz

mcp = FastMCP("GMAIL")

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
PORT = 8081

creds = None
if not creds or creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=PORT)

    with open("token.json", "w") as token:
        token.write(creds.to_json())
service = build("gmail", "v1", credentials=creds)


# def main():
#     creds = None
# # if os.path.exists('token.json'):
# #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file(
#             "credentials.json", SCOPES
#         )
#         creds = flow.run_local_server(port=8080)
        
#         # Save the credentials for the next run
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
    
#     try:
#         service = build("gmail", "v1", credentials = creds)
#         results = service.users().labels().list(userId="me").execute()
#         labels = results.get("labels", [])

#         if not labels:
#             print("No labels found")
#             return
#         print("Labels:")
#         for label in labels:
#             print(label['name'])    
        
#     except HttpError as error:
#         print(f'An error occured: {error}')

def gmail_create_message(to: str, sender: str, subject: str, content: str):
    """
    Create a message that can later be sent using the Gmail API
    Args:
        to (str): The email address of the user receiving the message
        sender (str): The email address of the user sending the message
        subject (str): The subject line of the email
        content (str): The actual content of the email message
    Returns:
        draft: A draft object that can later be sent as an email
    """
    message = EmailMessage()

    message.set_content(content)

    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"message": {"raw": encoded_message}}
    draft = (
        service.users().drafts().create(userId="me", body=create_message)
        .execute()
    )

    print(f'Draft id: {draft['id']}\nDraft message: {draft['message']}')

@mcp.tool()
def gmail_send_message(to: str, sender: str, subject: str, content: str):
    """
    Sends an email using the Gmail API
    Args:
        to (str): The email address of the user receiving the message
        sender (str): The email address of the user sending the message
        subject (str): The subject line of the email
        content (str): The actual content of the email message
    Returns:
    """
        
    message = EmailMessage()

    message.set_content(content)

    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    send_message = (
        service.users().messages().send(userId="me", body=create_message)
        .execute()
    )

    print(f'Message Id: {send_message['id']}')
    return f'Sent message: {send_message}'

if __name__ == '__main__':
    print("Starting Gmail server...")
    # gmail_send_message('asphaltlord123@gmail.com', 'pranav.batra2006@gmail.com', 'Test', 'This is a test email')
    mcp.run(transport='stdio')