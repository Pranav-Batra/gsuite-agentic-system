import os.path
import argparse
from mcp.server.fastmcp import FastMCP

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dateutil import parser
import pytz

mcp = FastMCP("GCAL")
PORT = 8081


# If modifying these scopes, delete the file token.json.
# This scope provides read-only access to calendars.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_credentials():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh-token', required=True)
    parser.add_argument('--client-id', required=True)
    parser.add_argument('--client-secret', required=True)
    args = parser.parse_args()

    creds = Credentials(
        token=None,
        refresh_token = args.refresh_token,
        token_uri = "https://oauth2.googleapis.com/token",
        client_id = args.client_id,
        client_secret = args.client_secret,
        scopes=SCOPES
    )
    return creds

creds = get_credentials()
service = build("calendar", "v3", credentials=creds)


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the summary and timezone of the user's primary calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        
            # You must have a 'credentials.json' file from the Google Cloud Console
            # for this flow to work.
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=PORT)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build the service object
        service = build("calendar", "v3", credentials=creds)

        # The calendarId 'primary' is a special alias for the user's main calendar.
        calendar_id = "primary"
        
        print(f"--- Getting info for calendar: {calendar_id} ---")
        
        # Call the Calendar API's 'calendars.get' method
        calendar_info = service.calendars().get(calendarId=calendar_id).execute()

        # Print the results
        print(f"✅ Success!")
        print(f"Summary: {calendar_info['summary']}")
        print(f"ID: {calendar_info['id']}")
        print(f"Time Zone: {calendar_info['timeZone']}")


    except HttpError as error:
        print(f"An error occurred: {error}")


@mcp.tool()
def gcal_get_main_calendar_info():
    """
    This tool is used to get basic information about the main/primary calendar of a user
    """
    calendar_id = "primary"
    
    print(f"--- Getting info for calendar: {calendar_id} ---")
    
    # Call the Calendar API's 'calendars.get' method
    calendar_info = service.calendars().get(calendarId=calendar_id).execute()

    # Print the results
    print(f"✅ Success!")
    print(f"Summary: {calendar_info['summary']}")
    print(f"ID: {calendar_info['id']}")
    print(f"Time Zone: {calendar_info['timeZone']}")


@mcp.tool()
def gcal_create_event_in_main_calendar(name: str, description: str, start_time: str,
                                        end_time: str):

    """
    This tool creates an event in the primary calendar
    Args:
        name (str): The name of the event
        description (str): A description of the event being set up
        start_time (str): A string representing the starting date and time of the event in a format supported by dateutil.parser
        end_time (str): A string representing the ending date and time of the event in a format supported by dateutil.parser
    """   
    calendar_id = "primary"
    timezone = "America/Los_Angeles"
    tz = pytz.timezone(timezone)

    start = parser.parse(start_time)
    end = parser.parse(end_time)

    start_dt = tz.localize(start)
    end_dt = tz.localize(end)

    event = {
        'summary': name,
        'description': description,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'America/Los_Angeles'
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'America/Los_Angeles'
        }

    }

    event = service.events().insert(calendarId='primary', body = event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    return f"Event created: {event.get('htmlLink')}"

if __name__ == "__main__":
    # gcal_create_event_in_main_calendar('test event', 'this event is testing the gcal api', "Aug 5 2025 10:15AM", "Aug 5 2025 10:45AM")
    print("Starting Google Calendar server...")
    mcp.run(transport='stdio')

# @mcp.resource("greeting://{name}")
# def get_greeting(name: str) -> str:
#     return f"Hello, {name}!"

# if __name__ == '__main__':
#     print("Starting server...")
#     mcp.run(transport = "stdio")