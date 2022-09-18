#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import sys

import confidential
import constants
import sync_operations
import operations_additional
import email_operations

if __name__ == "__main__":
    # Backup
    if constants.BACKUP_ENABLE:
        operations_additional.events_backup(sys.argv, "events_backup_source_jbg", confidential.CALENDAR_SOURCE)
        operations_additional.events_backup(sys.argv, "events_backup_target_jb", confidential.CALENDAR_TARGET)

    # Environment    
    execution_timestamp = datetime.utcnow().isoformat() + 'Z'
    updated_min = operations_additional.latest_run_updated_min(confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET)
    service = operations_additional.google_api_service(sys.argv, ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"])

    # Run
    events_df, events_df_execution, events_counter = sync_operations.events_move_import(service, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, updated_min=updated_min)  # Only after a specific time
    # events_move_import(sys.argv, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, time_range=TIME_RANGE, updated_min=UPDATED_MIN)  # Range of time to search for new updated events
    # events_move_import(sys.argv, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, time_range=TIME_RANGE)
    # events_move_import(sys.argv, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp)  # All import

    # Send email
    if constants.EMAIL_ENABLE and events_df_execution.shape[0]>0:
        email_operations.send_email(events_df, events_df_execution, events_counter, confidential.CALENDAR_SOURCE, confidential.CALENDAR_TARGET, execution_timestamp, updated_min=updated_min)

    pass