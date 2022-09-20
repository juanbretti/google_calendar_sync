#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import pandas as pd
import json
import os

import constants
import operations_additional
import event_operations

def events_move_import(service, calendar_source, calendar_target, execution_timestamp, time_range=None, updated_min=None):
    # Read and create `events_df`
    events_df, events_df_path, events_df_execution_path = operations_additional.read_events_df(calendar_source, calendar_target)

    # Initialization
    page_token = None
    events_df_execution = pd.DataFrame()
    events_counter ={
        'global': 0,
        'moved': 0, 
        'imported': 0, 
        'reimported': 0,
        'reimported_merged': 0, 
        'missing': 0, 
        'imported_sequence_error': 0,
        'cancelled': 0,
        'cancelled_previously_moved': 0,
        'already': 0,
        }

    while True:

        # Filter time range to operate with the events
        if time_range and updated_min:
            events = service.events().list(calendarId=calendar_source, pageToken=page_token, timeMin=time_range[0], timeMax=time_range[1], updatedMin=updated_min).execute()
        elif time_range and not updated_min:
            events = service.events().list(calendarId=calendar_source, pageToken=page_token, timeMin=time_range[0], timeMax=time_range[1]).execute()
        elif not time_range and updated_min:
            # If I set `updatedMin`, I also have to set `showDeleted`=False
            events = service.events().list(calendarId=calendar_source, pageToken=page_token, updatedMin=updated_min, showDeleted=True).execute()
        else:
            events = service.events().list(calendarId=calendar_source, pageToken=page_token).execute()

        # Iterate the 250 events in the page
        for event in events['items']:
            events_counter['global'] += 1
            operation_timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
            if constants.LOG_PRINT:
                print(f"> Reading {event['id']}")

            events_df_filtered = events_df[(events_df['id_source'] == event['id']) & (events_df['inserted_target'].isin(constants.EVENTS_STORED))].sort_values(by='operation_timestamp', ascending=False).head(1)

            if event['status'] == 'cancelled':
                event_type = 'cancelled'
                # Just getting warned about the `cancelled` event. No action is taking place.

                # To add information after the `cancelled` events. More likely, are events that were previously `moved`.
                if updated_min is not None:
                    events_df_filtered = events_df[(events_df['id_source'] == event['id']) & (events_df['inserted_target'] == 'moved') & (events_df['operation_timestamp'] <= updated_min)]
                else:
                    events_df_filtered = events_df[(events_df['id_source'] == event['id']) & (events_df['inserted_target'] == 'moved')]

                if events_df_filtered.shape[0]>0:
                    event_type = 'cancelled_previously_moved'
                    if 'summary' not in event:
                        event['summary'] = events_df_filtered['summary_source'].iloc[-1]  # I get the `summary` from the previous `moved` operation

                # Log
                event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter)
            
            elif events_df_filtered.shape[0] == 0:
                # Strange events missing `summary` or `start`
                if not set(['summary', 'start']).issubset(event):
                    event_type = 'missing'
                    # Log
                    event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter)

                # Fresh `move` or `import`
                else:
                    # Move
                    if event['organizer']['email'] == calendar_source:
                        event_type = 'moved'
                        # Add the `watermark` to the `event` at the `source`
                        event['description'] = event_operations.event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp)
                        # Update and move the `event` to `target`
                        updated_event = service.events().update(calendarId=calendar_source, eventId=event['id'], body=event).execute()
                        updated_event = service.events().move(calendarId=calendar_source, eventId=event['id'], destination=calendar_target, sendUpdates='none').execute()
                        # Log
                        event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter)

                    # Import
                    else:
                        event_type = 'imported'
                        # Add the `watermark` to the `event` at the temporary event
                        event['description'] = event_operations.event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp)
                        # Add `attendee` to be able to import
                        event['attendees'] = event_operations.event_attendees_update(event, calendar_target)
                        # Insert or fake-import
                        try:
                            event_add = service.events().import_(calendarId=calendar_target, body=event).execute()
                            event_target = service.events().get(calendarId=calendar_target, eventId=event['id']).execute()
                            # Log
                            event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter, event_target_updated=event_target['updated'])
                        except Exception as e:
                            # https://stackoverflow.com/a/63487429/3780957
                            # https://developers.google.com/calendar/api/guides/errors
                            if json.loads(e.content)['error']['message'] == 'Invalid sequence value. The specified sequence number is below the current sequence number of the resource. Re-fetch the resource and use its sequence number on the following request.':
                                event_type = 'imported_sequence_error'
                                # event['sequence'] = 0  # Is not the problem, there is something else...
                                event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter)
                            else:
                                # Unhandled error
                                raise e

            # `Reimport` or `sync`
            elif (events_df_filtered.shape[0]>0):
                event_target = service.events().get(calendarId=calendar_target, eventId=event['id']).execute()
                # source updated, target constant
                if (event['updated'] > events_df_filtered['updated_source']).any() & (event_target['updated'] == events_df_filtered['updated_target']).any():
                    event_type = 'reimported'
                    # Add the `watermark` to the `event` at the temporary event
                    event['description'] = event_operations.event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp)
                # source updated, target updated
                elif (event['updated'] > events_df_filtered['updated_source']).any() & (event_target['updated'] > events_df_filtered['updated_target']).any():
                    event_type = 'reimported_merged'
                    # Add the `watermark` to the `event` at the temporary event
                    event['description'] = event_operations.event_description_update(event, event_type, calendar_source, calendar_target, operation_timestamp, event_target)
                else:
                    event_type = 'already'

                if event_type in ['reimported', 'reimported_merged']:
                    # Add `attendee` to be able to import
                    event['attendees'] = event_operations.event_attendees_update(event, calendar_target)
                    # Insert or fake-import
                    event_add = service.events().import_(calendarId=calendar_target, body=event).execute()

                # Log
                if event_type in ['reimported', 'reimported_merged']:
                    event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter, event_target_updated=event_target['updated'])
                elif event_type == 'already':
                    event_log, events_counter, _ = operations_additional.event_df_log(calendar_source, event, calendar_target, operation_timestamp, event_type, execution_timestamp, events_counter)

            else:
                print(f"Exception 1 {event['id']}")

            # Write log
            events_df = pd.concat([events_df, event_log], ignore_index=True)
            events_df_execution = pd.concat([events_df_execution, event_log], ignore_index=True)
            event_log[events_df.columns].to_csv(events_df_path, index=False, mode='a', header=not os.path.exists(events_df_path))  # Resort columns, later export with `mode='a'` (append) https://stackoverflow.com/a/17975690/3780957

        page_token = events.get('nextPageToken')
        if not page_token:
            break

    # Write log
    events_df.to_csv(events_df_path, index=False)
    events_df_execution.to_csv(events_df_execution_path, index=False)

    if constants.LOG_PRINT:
        print(f"Synchronization complete from `{calendar_source}` to `{calendar_target}`")
        print(', '.join(f'{k}: {v}' for k, v in events_counter.items()))

    return events_df, events_df_execution, events_counter
