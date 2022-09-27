#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from zoneinfo import ZoneInfo
import sys

import confidential
import constants
import sync_operations
import operations_additional
import email_operations

if __name__ == "__main__":
    # Environment
    execution_timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

    if constants.LOG_PRINT:
        execution_timestamp_formatted = datetime.datetime.fromisoformat(execution_timestamp[:-1]).astimezone(ZoneInfo(constants.TIME_ZONE)).strftime(constants.DATE_FORMAT)
        print(f">>> execution_timestamp_formated: `{execution_timestamp_formatted}` <<<")

    # Backup
    if constants.BACKUP_ENABLE:
        operations_additional.events_backup(sys.argv, "events_backup_source_jbg", confidential.CALENDAR_SOURCE)
        operations_additional.events_backup(sys.argv, "events_backup_target_jb", confidential.CALENDAR_TARGET)

    # Environment
    updated_min = operations_additional.latest_run_updated_min(confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET)
    service = operations_additional.google_api_service(sys.argv, ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"])

    # Run
    _, events_df_execution, events_counter = sync_operations.events_move_import(service, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, updated_min=updated_min)  # Only after a specific time
    # events_move_import(sys.argv, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, time_range=TIME_RANGE, updated_min=UPDATED_MIN)  # Range of time to search for new updated events
    # events_move_import(sys.argv, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, time_range=TIME_RANGE)
    # events_move_import(sys.argv, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp)  # All import

    # Send email
    if constants.EMAIL_ENABLE and events_df_execution.shape[0]>0:
        email_operations.send_email(events_df_execution, events_counter, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, updated_min=updated_min)
