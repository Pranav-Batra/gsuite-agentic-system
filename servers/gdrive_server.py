import os.path
import io

from mcp.server.fastmcp import FastMCP

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
 

mcp = FastMCP("GDRIVE")

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]

# If modifying these scopes, delete the file token.json

creds = None
if not creds or creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=8080)

    with open("token.json", "w") as token:
        token.write(creds.to_json())
service = build("drive", "v3", credentials=creds)

@mcp.tool()
def gdrive_get_first_n_files(files_to_print: int = 10) -> str:
    """
    Retrieve basic information about a set amount of files from the user's Google Drive
    Args:
        files_to_print (int): The number of files to retrieve information about
    Returns:
        result: A string clarifying if the retrieval was successful or not
    """
    try:
    # Call the Drive v3 API
        results = (
            service.files()
            .list(pageSize=files_to_print, fields="nextPageToken, files(id, name)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return "No files found."
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']})")
        return "Succesfully retrieved files."
    except HttpError as error:
    # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")
        return f"An error occured: {error}"

@mcp.tool()
def gdrive_download_file(user_file_id: str, output_file_name: str) -> str:
    """
    Download a specific file from the user's Google Drive and save to a user specified path
    Args:
        user_file_id (str): the file_id of the file that will be downloaded
        output_file_name (str): the path on the local machine that the downloaded file will be written to
    Returns:
        file_io (str): The downloaded file's io content if it exists, otherwise a message of failure.
    """
    try:
    # create drive api client
        file_id = user_file_id
        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None
        return "Failed to download."

    if file:
        with open(output_file_name, 'wb') as f:
            f.write(file.getvalue())
    return file.getvalue()


@mcp.tool(
    name="gdrive_search_file",
    description=(
        "Search the user's Google Drive using the Drive API query syntax.\n"
        "Examples of valid queries:\n"
        "• Files with the name 'hello': name = 'hello'\n"
        "• Files with a name containing 'hello' and 'goodbye': name contains 'hello' and name contains 'goodbye'\n"
        "• Files with a name that does not contain 'hello': not name contains 'hello'\n"
        "• Files containing the text 'important' and in the trash: fullText contains 'important' and trashed = true\n"
        "• Files containing the word 'hello': fullText contains 'hello'\n"
        "• Files not containing the word 'hello': not fullText contains 'hello'\n"
        "• Files containing the exact phrase 'hello world': fullText contains '\"hello world\"'\n"
        "• Files with a query containing '\\\\' (e.g., '\\\\authors'): fullText contains '\\\\authors'\n"
        "• Files that are folders: mimeType = 'application/vnd.google-apps.folder'\n"
        "• Files that are not folders: mimeType != 'application/vnd.google-apps.folder'\n"
        "• Files modified after a given date (UTC): modifiedTime > '2012-06-04T12:00:00'\n"
        "You can combine multiple conditions with AND/OR."
    ),
)
def gdrive_search_file(query: str, max_results: int = 10):
    """
    Search Google Drive using the provided query string.
    Args:
        query (str): Google Drive API query string.
        max_results (int): Max number of files to return.
    Returns:
        list: Matching files with their IDs and names.
    """
    try:
    # create drive api client
        files = []
        page_token = None
        while True:
        # pylint: disable=maybe-no-member
            response = (
                service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                )
                .execute()
            )
            for file in response.get("files", []):
                # Process change
                print(f'Found file: {file.get("name")}, {file.get("id")}')
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break

    except HttpError as error:
        print(f"An error occurred: {error}")
        files = None

    return files

@mcp.tool()
def gdrive_share_files(file_id: str, emails: list[str], role: str = "reader") -> str:
    """
    Share a Google Drive file with one or more accounts.

    Args:
        file_id (str): The ID of the file to share.
        emails (list[str]): A list of email addresses to share the file with.
        role (str): The access level to grant (e.g., "reader", "writer", "commenter").
    
    Returns:
        result (str): A string clarifying if the sharing action was successful.
    """
    try:
        # Iterate through the email list and create permissions
        for email in emails:
            permission = {
                "type": "user",
                "role": role,
                "emailAddress": email,
            }
            service.permissions().create(
                fileId=file_id,
                body=permission,
                fields="id",
            ).execute()
            print(f"Shared file {file_id} with {email} as {role}")

        return f"Successfully shared file {file_id} with {len(emails)} account(s)."

    except HttpError as error:
        # TODO(developer) – Handle errors from drive API
        print(f"An error occurred: {error}")
        return f"An error occurred: {error}"

if __name__ == "__main__":
    vandertramp = (gdrive_search_file(query="name contains 'VANDERTRAMP'"))[0]
    gdrive_share_files(vandertramp['id'], ['asphaltlord123@gmail.com'], 'reader')
