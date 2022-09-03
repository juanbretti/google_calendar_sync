#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://console.cloud.google.com/apis/api/calendar-json.googleapis.com/quotas?authuser=1&project=skilful-charmer-357720
# https://github.com/googleapis/google-api-python-client/tree/main/samples/calendar_api
# https://developers.google.com/calendar/api/v3/reference/events

from oauth2client import client
from googleapiclient import sample_tools
import sys
from datetime import datetime
import pandas as pd
import json

from bs4 import BeautifulSoup
import difflib
import os
import re

import personal

def calendar_list(argv):
    # Authenticate and construct service.
    service, flags = sample_tools.init(
        argv,
        "calendar",
        "v3",
        __doc__,
        __file__,
        scope = "https://www.googleapis.com/auth/calendar.readonly",
    )

    try:
        page_token = None
        while True:
            calendar_list = service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list["items"]:
                print(calendar_list_entry['summary'], calendar_list_entry['id'])
            page_token = calendar_list.get("nextPageToken")
            if not page_token:
                break

    except client.AccessTokenRefreshError:
        print(
            "The credentials have been revoked or expired, please re-run"
            "the application to re-authorize."
        )

def events_backup(argv, file_name, calendar):
    # Authenticate and construct service.
    service, flags = sample_tools.init(
        argv,
        "calendar",
        "v3",
        __doc__,
        __file__,
        scope = "https://www.googleapis.com/auth/calendar.readonly",
    )

    page_token = None
    file_name_complete = personal.PATH_DATA + "/" + file_name + "_" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + ".json"
    text_file = open(file_name_complete, mode="w", encoding="utf-8")
    events_concatenate = {}
    events_counter = 0

    while True:
        events = service.events().list(calendarId=calendar, pageToken=page_token).execute()
        for event in events['items']:
            events_concatenate.update({"Event_" + str(events_counter): event}) 
            events_counter += 1
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    text_file.write(json.dumps(events_concatenate))
    text_file.close()
    print(f"Export complete of `{calendar}` on `{file_name_complete}`")

# def event_description_remove_html_tags(raw_html):
#     raw_html = re.sub('<br\s*?>', os.linesep, raw_html)
#     # clean_text = BeautifulSoup(raw_html, "lxml").text
#     clean_text = BeautifulSoup(raw_html, "html.parser").text
#     clean_text = clean_text.splitlines()
#     return clean_text

# def event_description_text_diff(old, new):
#     diff = difflib.ndiff(event_description_remove_html_tags(old), event_description_remove_html_tags(new))
#     diff = '\n'.join(list(diff))
#     return diff

def event_description_update(event, custom_flag, calendar_source, calendar_target, operation_timestamp, event_target=None):
    # Add `watermark` if there is any `recurringEventId`
    if 'recurringEventId' in event:
        watermark_recurringEventId = f"recurringEventId: {str(event['recurringEventId'])}<br>"
    else:
        watermark_recurringEventId = ""

    # Add `watermark`
    watermark = f"|{custom_flag.upper()}|<br>calendar_source: {calendar_source}<br>calendar_target: {calendar_target}<br>id_source: {event['id']}<br>updated_source: {event['updated']}<br>operation_timestamp: {operation_timestamp}<br>{watermark_recurringEventId}|/{custom_flag.upper()}|"
    if 'description' in event:
        event['description'] = f"{watermark}<br><br><br>{str(event['description'])}"
    else:
        event['description'] = watermark

    # To merge the `event_target` and the new `event_source` `description`
    if event_target:
        event['description'] = f"{event['description']}<br><br><br>|PREVIOUSLY|<br>{event_target['description']}"
        # event_target_old = event_target['description'].split("|/REIMPORTED|<br><br><br>")[1]
        # event['description'] = event_description_text_diff(event_target_old, event['description'])

    return event['description']

def event_attendees_update(event, calendar_target):
    # Add `attendee` to be able to import
    self_attendee = {"email": calendar_target, "displayName": "Juan Pedro Bretti Mandarano (calendar_target)", "self": True, "responseStatus": "accepted"}
    if 'attendees' in event:
        event['attendees'].append(self_attendee)
    else:
        event['attendees'] = [self_attendee]
    
    return event['attendees']

def event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_case, events_counter, event_target_updated = None):
    event_log = pd.DataFrame({'calendar_source': calendar_source, 'id_source': event['id'], 'updated_source': event['updated'], 'updated_target': event_target_updated, 'calendar_target': calendar_target, 'operation_timestamp': operation_timestamp, 'inserted_target': event_type, 'execution_timestamp': execution_timestamp}, index=[0])
    events_counter_case += 1
    print_statement = f"{event_type}: {event['id']}. events_counter: {events_counter + 1}"
    print(print_statement)

    return event_log, events_counter_case, print_statement

def events_move_import(argv, calendar_source, calendar_target, execution_timestamp):
    service, flags = sample_tools.init(
        argv,
        "calendar",
        "v3",
        __doc__,
        __file__,
        scope = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"],
    )
    
    calendar_source_target_path = personal.PATH_DATA + "/" + calendar_source.split("@")[0] + "-" + calendar_target.split("@")[0] + ".csv"
    try:
        events_df = pd.read_csv(calendar_source_target_path)
        print('Reading `csv`')
    except:
        events_df = pd.DataFrame()
        events_df['inserted_target'] = events_df['id_source'] = events_df['operation_timestamp'] = events_df['updated_source'] = None
        print('Creating `csv`')
    
    page_token = None
    events_counter_imported = events_counter_moved = events_counter_missing = events_counter_already = events_counter_reimported = events_counter_reimported_merged = 0

    while True:
        events = service.events().list(calendarId=calendar_source, pageToken=page_token).execute()
        for events_counter, event in enumerate(events['items']):
            operation_timestamp = datetime.utcnow().isoformat() + 'Z'
            events_df_filtered = events_df[(events_df['id_source'] == event['id']) & (events_df['inserted_target'].isin(['moved', 'imported', 'reimported', 'reimported_merged']))].sort_values(by='operation_timestamp', ascending=False).head(1)

            if events_df_filtered.shape[0] == 0:
                # Strange events missing `summary` or `start`
                if not set(['summary', 'start']).issubset(event):
                    event_type = 'missing'
                    # Log
                    event_log, events_counter_missing, _ = event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_missing, events_counter)

                # Fresh `move` or `import`
                else:
                    # Move
                    if event['organizer']['email'] == calendar_source:
                        event_type = 'moved'
                        # Add the `watermark` to the `event` at the `source`
                        event['description'] = event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp)
                        # Update and move the `event` to `target`
                        updated_event = service.events().update(calendarId=calendar_source, eventId=event['id'], body=event).execute()
                        updated_event = service.events().move(calendarId=calendar_source, eventId=event['id'], destination=calendar_target, sendUpdates='none').execute()
                        # Log
                        event_log, events_counter_moved, _ = event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_moved, events_counter)

                    # Import
                    else:
                        event_type = 'imported'
                        # Add the `watermark` to the `event` at the temporary event
                        event['description'] = event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp)
                        # Add `attendee` to be able to import
                        event['attendees'] = event_attendees_update(event, calendar_target)
                        # Insert or fake-import
                        event_add = service.events().import_(calendarId=calendar_target, body=event).execute()
                        event_target = service.events().get(calendarId=calendar_target, eventId=event['id']).execute()
                        # Log
                        event_log, events_counter_imported, _ = event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_imported, events_counter, event_target['updated'])

            # `Reimport` or `sync`
            elif (events_df_filtered.shape[0]>0):
                event_target = service.events().get(calendarId=calendar_target, eventId=event['id']).execute()
                
                # source updated, target constant
                if (event['updated'] > events_df_filtered['updated_source']).any() & (event_target['updated'] == events_df_filtered['updated_target']).any():
                    event_type = 'reimported'
                    # Add the `watermark` to the `event` at the temporary event
                    event['description'] = event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp)
                # source updated, target updated
                elif (event['updated'] > events_df_filtered['updated_source']).any() & (event_target['updated'] > events_df_filtered['updated_target']).any():
                    event_type = 'reimported_merged'
                    # Add the `watermark` to the `event` at the temporary event
                    event['description'] = event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp, event_target)
                else:
                    event_type = 'already'

                if event_type in ['reimported', 'reimported_merged']:
                    # Add `attendee` to be able to import
                    event['attendees'] = event_attendees_update(event, calendar_target)
                    # Insert or fake-import
                    event_add = service.events().import_(calendarId=calendar_target, body=event).execute()

                # Log
                if event_type == 'reimported':
                    event_log, events_counter_reimported, _ = event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_reimported, events_counter, event_target['updated'])
                elif event_type == 'reimported_merged':
                    event_log, events_counter_reimported_merged, _ = event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_reimported_merged, events_counter, event_target['updated'])
                elif event_type == 'already':
                    event_log, events_counter_already, _ = event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter_already, events_counter)

            else:
                print('Exception 1')
                pass

            # Write log
            events_df = pd.concat([events_df, event_log], ignore_index=True)
            events_df.to_csv(calendar_source_target_path, index=False)

        page_token = events.get('nextPageToken')
        if not page_token:
            break

    # Write log
    events_df.to_csv(calendar_source_target_path, index=False)

    print(f"Copy complete from `{calendar_source}` to `{calendar_target}`")
    print(f"events_counter {events_counter+1}, moved {events_counter_moved}, imported {events_counter_imported}, reimported {events_counter_reimported}, reimported_merged {events_counter_reimported_merged}, missing {events_counter_missing}, already {events_counter_already}")

if __name__ == "__main__":
    execution_timestamp = datetime.utcnow().isoformat() + 'Z'

    # calendar_list(sys.argv)
    events_backup(sys.argv, "events_backup_source_gw", personal.CALENDAR_SOURCE)
    events_backup(sys.argv, "events_backup_target_gw", personal.CALENDAR_TARGET)
    events_move_import(sys.argv, personal.CALENDAR_SOURCE, personal.CALENDAR_TARGET, execution_timestamp)

    pass
