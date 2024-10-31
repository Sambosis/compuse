from __future__ import print_function
import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Event data
events = [
    # Friday, October 25th
    {"summary": "Warren Off", "start": "2023-10-25T00:00:00", "end": "2023-10-25T23:59:59"},
    {"summary": "Pick Cam up at school", "start": "2023-10-25T12:00:00", "end": "2023-10-25T12:30:00"},
    {"summary": "Pick Winter up", "start": "2023-10-25T15:30:00", "end": "2023-10-25T16:00:00"},
    {"summary": "Work on getting rid of clothes", "start": "2023-10-25T16:00:00", "end": "2023-10-25T18:00:00"},
    {"summary": "Do garage, closets", "start": "2023-10-25T18:00:00", "end": "2023-10-25T20:00:00"},

    # Saturday, October 26th
    {"summary": "Warren Work 8-5", "start": "2023-10-26T08:00:00", "end": "2023-10-26T17:00:00"},
    {"summary": "Pick up Truck", "start": "2023-10-26T09:00:00", "end": "2023-10-26T09:30:00"},
    {"summary": "Load Truck", "start": "2023-10-26T10:00:00", "end": "2023-10-26T12:00:00"},
    {"summary": "Take bins to storage", "start": "2023-10-26T13:00:00", "end": "2023-10-26T15:00:00"},

    # Sunday, October 27th
    {"summary": "Warren Off", "start": "2023-10-27T00:00:00", "end": "2023-10-27T23:59:59"},
    {"summary": "Load Truck", "start": "2023-10-27T09:00:00", "end": "2023-10-27T11:00:00"},
    {"summary": "Clean out 6 closets", "start": "2023-10-27T11:00:00", "end": "2023-10-27T13:00:00"},
    {"summary": "Clear garage", "start": "2023-10-27T13:00:00", "end": "2023-10-27T15:00:00"},
    {"summary": "Andrew help take Amoire to Shannon’s", "start": "2023-10-27T15:00:00", "end": "2023-10-27T17:00:00"},

    # Monday, October 28th
    {"summary": "Moving guys to load upstairs & sofa & chairs in truck", "start": "2023-10-28T09:00:00", "end": "2023-10-28T12:00:00"},
    {"summary": "Warren Off", "start": "2023-10-28T00:00:00", "end": "2023-10-28T23:59:59"},

    # Tuesday, October 29th
    {"summary": "Warren Off", "start": "2023-10-29T00:00:00", "end": "2023-10-29T23:59:59"},
    {"summary": "Clean House", "start": "2023-10-29T09:00:00", "end": "2023-10-29T12:00:00"},
    {"summary": "Spackle & paint", "start": "2023-10-29T12:00:00", "end": "2023-10-29T15:00:00"},

    # Wednesday, October 30th
    {"summary": "Walk through", "start": "2023-10-30T09:00:00", "end": "2023-10-30T09:30:00"},
    {"summary": "Settlement", "start": "2023-10-30T10:00:00", "end": "2023-10-30T11:00:00"},
    {"summary": "Warren Off", "start": "2023-10-30T00:00:00", "end": "2023-10-30T23:59:59"},
    {"summary": "Sam Off", "start": "2023-10-30T00:00:00", "end": "2023-10-30T23:59:59"},
    {"summary": "Take dogs to Sam’s house", "start": "2023-10-30T19:30:00", "end": "2023-10-30T20:00:00"},

    # Thursday, October 31st
    {"summary": "Painter Estimate", "start": "2023-10-31T09:00:00", "end": "2023-10-31T10:00:00"},
    {"summary": "Warren Off", "start": "2023-10-31T00:00:00", "end": "2023-10-31T23:59:59"},
    {"summary": "Sam Off", "start": "2023-10-31T00:00:00", "end": "2023-10-31T23:59:59"},

    # Friday, November 1st
    {"summary": "Meet with Contractor", "start": "2023-11-01T09:00:00", "end": "2023-11-01T10:00:00"},
    {"summary": "ADT 11-1", "start": "2023-11-01T11:00:00", "end": "2023-11-01T13:00:00"},
    {"summary": "Warren Off", "start": "2023-11-01T00:00:00", "end": "2023-11-01T23:59:59"},
    {"summary": "Sam off - Schools Closed. Sam has kids", "start": "2023-11-01T00:00:00", "end": "2023-11-01T23:59:59"},

    # Saturday, November 2nd
    {"summary": "Xfinity installed", "start": "2023-11-02T09:00:00", "end": "2023-11-02T12:00:00"},

    # Monday, November 4th
    {"summary": "Contractor to start Projects", "start": "2023-11-04T09:00:00", "end": "2023-11-04T17:00:00"},
    {"summary": "Kids off School", "start": "2023-11-04T00:00:00", "end": "2023-11-04T23:59:59"},
    {"summary": "Watch kids at our house", "start": "2023-11-04T09:00:00", "end": "2023-11-04T17:00:00"},
    {"summary": "Warren Off", "start": "2023-11-04T00:00:00", "end": "2023-11-04T23:59:59"},

    # Tuesday, November 5th
    {"summary": "Contractor working", "start": "2023-11-05T09:00:00", "end": "2023-11-05T17:00:00"},
    {"summary": "Kids off school", "start": "2023-11-05T00:00:00", "end": "2023-11-05T23:59:59"},
    {"summary": "Watch Kids at our house", "start": "2023-11-05T09:00:00", "end": "2023-11-05T17:00:00"},
    {"summary": "Election Day", "start": "2023-11-05T09:00:00", "end": "2023-11-05T17:00:00"},

    # Wednesday, November 6th
    {"summary": "Contractor working", "start": "2023-11-06T09:00:00", "end": "2023-11-06T17:00:00"},
    {"summary": "Maggie Vet Appointment", "start": "2023-11-06T17:00:00", "end": "2023-11-06T18:00:00"},

    # Thursday, November 7th
    {"summary": "Contractor working", "start": "2023-11-07T09:00:00", "end": "2023-11-07T17:00:00"},

    # Friday, November 8th
    {"summary": "Contractor working", "start": "2023-11-08T09:00:00", "end": "2023-11-08T17:00:00"},
    {"summary": "Buffy Vet Appointment", "start": "2023-11-08T11:00:00", "end": "2023-11-08T12:00:00"},

    # Saturday, November 9th
    {"summary": "Contractor working", "start": "2023-11-09T09:00:00", "end": "2023-11-09T17:00:00"},
    {"summary": "April’s Celebration", "start": "2023-11-09T11:00:00", "end": "2023-11-09T12:30:00"},

    # Monday, November 11th
    {"summary": "Kids off school", "start": "2023-11-11T00:00:00", "end": "2023-11-11T23:59:59"},
    {"summary": "Watch Kids at our house", "start": "2023-11-11T09:00:00", "end": "2023-11-11T17:00:00"},

    # Friday, November 15th
    {"summary": "Princess Vet Appointment", "start": "2023-11-15T10:00:00", "end": "2023-11-15T11:00:00"},

    # Wednesday, November 27th
    {"summary": "Schools out 3 hours early", "start": "2023-11-27T12:00:00", "end": "2023-11-27T15:00:00"},

    # Friday, November 29th
    {"summary": "Schools off", "start": "2023-11-29T00:00:00", "end": "2023-11-29T23:59:59"}
]
#AIzaSyCwpbB9cSu-hp4KBaERn41Z-XDqXjWZyFM
def create_event(service, event_data):
    event = {
        'summary': event_data['summary'],
        'start': {
            'dateTime': event_data['start'],
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': event_data['end'],
            'timeZone': 'America/New_York',
        },
        'attendees': [
            {'email': 'sheilashan1008@gmail.com'},
        ],
    }
    event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
    print(f"Event created: {event.get('htmlLink')}")

def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Loop through the events and create them
    for event_data in events:
        create_event(service, event_data)

if __name__ == '__main__':
    main()