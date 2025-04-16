"""
Date: 2025-04-16
Last Modified: 2025-04-16
Description: Google Drive API Integration with Python (Object-Oriented Approach)

This program provides an object-oriented implementation for interacting with Google Drive using the Google Drive API.
It includes functionality for uploading, downloading, searching, and managing files and folders on Google Drive.

Key Features:
1. **Authentication**:
   - Authenticates the user using OAuth 2.0.
   - Stores credentials in a `token.json` file for reuse.

2. **File Management**:
   - List files in the user's Google Drive.
   - Search for files based on MIME type or other criteria.
   - Download files from Google Drive.
   - Upload files to Google Drive.
   - Upload files to a specific folder in Google Drive.

3. **Folder Management**:
   - Create folders in Google Drive.
   - Create shortcuts to files or folders.

4. **Export Files**:
   - Export Google Workspace documents (e.g., Google Docs, Sheets) to PDF format.

5. **Error Handling**:
   - Handles errors from the Google Drive API and provides meaningful error messages.

6. **Static Utility Methods**:
   - Includes a utility method to write downloaded content to a local file.

Requirements:
- Python libraries: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`.
- A `credentials.json` file for Google Drive API authentication.
- A valid `token.json` file will be created after the first authentication.

How to Use:
1. Place the `credentials.json` file in the same directory as this script.
2. Run the script to authenticate and generate a `token.json` file.
3. Use the provided methods to interact with Google Drive:
   - `listFile()`: List files in Google Drive.
   - `download_file(file_id)`: Download a file by its ID.
   - `upload_basic(file_name)`: Upload a file to the root directory.
   - `upload_to_folder(file_name, folder_id)`: Upload a file to a specific folder.
   - `create_folder(folder_name)`: Create a folder in Google Drive.
   - `search_file()`: Search for files in Google Drive.
   - `export_pdf(file_id)`: Export a Google Workspace document to PDF format.

Note:
- Ensure that the `credentials.json` file is properly configured with the required scopes.
- The program assumes that the user has enabled the Google Drive API for their project in the Google Cloud Console.
"""

from __future__ import print_function

import io
import os
import os.path

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload


###################
class gDrive:
    # credential token
    def __init__(self):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        # SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

        self.creds = None

        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file(
                "token.json", SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

    def listFile(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        try:
            service = build("drive", "v3", credentials=self.creds)

            # Call the Drive v3 API
            results = (
                service.files()
                .list(pageSize=100, fields="nextPageToken, files(id, name)")
                .execute()
            )
            items = results.get("files", [])

            if not items:
                print("No files found.")
                return
            print("Files:")
            for item in items:
                print("{0} ({1})".format(item["name"], item["id"]))

            print("Finished listing files.\n")
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f"An error occurred: {error}")

    def download_file(self, real_file_id):
        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)

            file_id = real_file_id

            # pylint: disable=maybe-no-member
            request = service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")

            print(f"Finished downloading file {file_id}.\n")
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        return file.getvalue()

    @staticmethod
    def writeFile(fileName, content):
        with open(fileName, "wb") as f:
            f.write(content)

    def upload_basic(self, fileName):
        """Insert new file.
        Returns : Id's of the file uploaded

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """

        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)

            # fileName = "sink.jpg"
            file_metadata = {"name": fileName}
            media = MediaFileUpload(fileName, mimetype="image/jpg", resumable=True)
            # pylint: disable=maybe-no-member
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f'File ID: {file.get("id")}')
            print(f"Finished uploading file {file.get("id")}.\n")
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        return file.get("id")

    def upload_to_folder(self, fn, folder_id):
        """Upload a file to the specified folder and prints file ID, folder ID
        Args: Id of the folder
        Returns: ID of the file uploaded

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)

            file_metadata = {"name": fn.split("/")[-1], "parents": [folder_id]}
            media = MediaFileUpload(fn, resumable=True)
            # pylint: disable=maybe-no-member
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f'File ID: "{file.get("id")}".')
            print(f"Finished uploading to folder {folder_id}.\n")

            return file.get("id")

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def search_file(self):
        """Search file in drive location

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        #   creds, _ = google.auth.default()
        # creds = identify()

        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)
            files = []
            page_token = None
            while True:
                # pylint: disable=maybe-no-member
                response = (
                    service.files()
                    .list(
                        q="mimeType='image/jpeg'",
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
            print("Finished searching files.\n")
        except HttpError as error:
            print(f"An error occurred: {error}")
            files = None

        return files

    def export_pdf(self, real_file_id):
        """Download a Document file in PDF format.
        Args:
            real_file_id : file ID of any workspace document format file
        Returns : IO object with location

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """

        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)

            file_id = real_file_id

            # pylint: disable=maybe-no-member
            request = service.files().export_media(
                fileId=file_id, mimeType="application/pdf"
            )
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}.")
            print("Finished exporting PDF.\n")
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        return file.getvalue()

    def create_folder(self, folderName):
        """Create a folder and prints the folder ID
        Returns : Folder Id

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """

        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)
            file_metadata = {
                "name": folderName,
                "mimeType": "application/vnd.google-apps.folder",
            }

            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, fields="id").execute()
            print(f'Folder ID: "{folderName}".')
            print("Finished creating folder.\n")
            return file.get("id")

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def create_shortcut(self, shortcutName, folder_id):
        """Create a third party shortcut

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        #   creds, _ = google.auth.default()

        try:
            # create drive api client
            service = build("drive", "v3", credentials=self.creds)
            file_metadata = {
                "name": shortcutName,
                "mimeType": "application/vnd.google-apps.drive-sdk",
                "parents": [folder_id],
            }

            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, fields="id").execute()
            print(f'File ID: {file.get("id")}')
            print("Finished creating shortcut.\n")
        except HttpError as error:
            print(f"An error occurred: {error}")
        return file.get("id")


if __name__ == "__main__":
    gdrive = gDrive()
    gdrive.listFile()
    gdrive.search_file()
    value = gdrive.download_file("1fRfATbOPyhDy-GmCsxwPsJlypWKndKup")
    gdrive.writeFile("dog1.jpg", value)
    gdrive.upload_basic("stream.asx")
    foid = gdrive.create_folder("Upload")
    gdrive.upload_to_folder("sink.jpg", foid)
    gdrive.create_shortcut("Project Plan Shortcut", foid)

    # value = gDrive.export_pdf(real_file_id="1Xh2VQF3iJ-Io2_GtNTcw6sXnoudSBvMo")
    # gDrive.writeFile("sf.pdf", value)
