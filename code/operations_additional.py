#!/usr/bin/env python
# -*- coding: utf-8 -*-

from oauth2client import client
from googleapiclient import sample_tools
import datetime
from zoneinfo import ZoneInfo
import json
import pandas as pd

import confidential
import constants

def google_api_service(argv, scope):
    service, flags = sample_tools.init(
        argv,
        "calendar",
        "v3",
        __doc__,
        __file__,
        scope = scope,
    )
    return service

def calendar_list(argv):
    service = google_api_service(argv, "https://www.googleapis.com/auth/calendar.readonly")

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

def events_backup(argv, file_name, calendar, show_deleted=False):
    service = google_api_service(argv, "https://www.googleapis.com/auth/calendar.readonly")

    page_token = None
    file_name_complete = confidential.PATH_DATA + "/" + file_name + "_" + datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + ".json"
    text_file = open(file_name_complete, mode="w", encoding="utf-8")
    events_concatenate = {}
    events_counter = 0

    while True:
        events = service.events().list(calendarId=calendar, pageToken=page_token, showDeleted=show_deleted).execute()
        for event in events['items']:
            events_concatenate.update({"Event_" + str(events_counter): event}) 
            events_counter += 1
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    text_file.write(json.dumps(events_concatenate))
    text_file.close()
    
    if constants.LOG_PRINT:
        print(f"Export complete of `{calendar}` on `{file_name_complete}`")

def read_events_df(calendar_source, calendar_target):
    events_df_path = confidential.PATH_DATA + "/" + calendar_source.split("@")[0] + "-" + calendar_target.split("@")[0] + ".csv"
    events_df_execution_path = confidential.PATH_DATA + "/" + calendar_source.split("@")[0] + "-" + calendar_target.split("@")[0] + "_execution.csv"
    try:
        events_df = pd.read_csv(events_df_path)
        if constants.LOG_PRINT:
            print('Reading `csv`')
    except: 
        events_df = pd.DataFrame(columns=['inserted_target', 'id_source', 'operation_timestamp', 'updated_source'])
        if constants.LOG_PRINT:
            print('Creating `csv`')

    return events_df, events_df_path, events_df_execution_path

def latest_run_updated_min(calendar_source, calendar_target, updated_min = constants.UPDATED_MIN):
    events_df, _, _ = read_events_df(calendar_source, calendar_target)
    if events_df.shape[0]>0:
        latest_run_time = events_df['operation_timestamp'].max()
    else:
        latest_run_time = input("Type date as `2022-08-31T00:00:00Z`")
        if latest_run_time == "":
            latest_run_time = updated_min
    
    if constants.LOG_PRINT:
        latest_run_time_formatted = datetime.datetime.fromisoformat(latest_run_time[:-1]).astimezone(ZoneInfo(constants.TIME_ZONE)).isoformat()
        print(f"Updated min `{latest_run_time_formatted}`")

    return latest_run_time

def event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter, event_target_updated = None):
    if event_type in ['missing', 'cancelled']:
        event['updated'] = event_target_updated = None

    if 'summary' not in event:
        event['summary'] = ""

    event_log = pd.DataFrame({
        'calendar_source': calendar_source,
        'id_source': event['id'],
        'updated_source': event['updated'],
        'summary_source': event['summary'],
        
        'calendar_target': calendar_target,
        'updated_target': event_target_updated,
        'inserted_target': event_type,
        
        'operation_timestamp': operation_timestamp,
        'execution_timestamp': execution_timestamp,
        }, index=[0])
    events_counter[event_type] += 1
    
    if constants.LOG_PRINT:
        print_statement = f"{event_type}: {event['id']}. events_counter_global: {events_counter['global']}."
        print(print_statement)

    return event_log, events_counter, print_statement

