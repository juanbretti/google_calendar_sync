#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import difflib
import os
import re

import constants
import confidential

def event_description_remove_html_tags(raw_html):
    raw_html = re.sub('<br\s*?>', os.linesep, raw_html)
    # clean_text = BeautifulSoup(raw_html, "lxml").text  # Runtime issues with "lxml"
    clean_text = BeautifulSoup(raw_html, "html.parser").text
    clean_text = clean_text.splitlines()
    return clean_text

def event_description_text_diff(old, new):
    diff = difflib.ndiff(event_description_remove_html_tags(old), event_description_remove_html_tags(new))
    diff = '\n'.join(list(diff))
    return diff

def clean_previous(text, events=constants.EVENTS_STORED, previous=constants.PREVIOUS, diff=constants.DIFF, min_for_first_search=constants.MIN_FOR_FIRST_SEARCH):
    for event_ in events:
        event_search = text.find(f"|{event_.upper()}|")
        event_search_end = text.find(f"|/{event_.upper()}|") + len(event_) + 3  # 3: |+/+|, three symbols
        second_search_diff = text.find(f"|{diff}|")
        second_search_previous = text.find(f"|{previous}|")

        if (event_search > 0) and (event_search < min_for_first_search):
            if (second_search_diff < second_search_previous) and (second_search_diff > event_search):
                text_clean = text[event_search_end:second_search_diff]
                break
            elif (second_search_previous < second_search_diff) and (second_search_previous > event_search):
                text_clean = text[event_search_end:second_search_previous]
                break
            elif (second_search_previous == second_search_diff) and (second_search_previous == -1):
                text_clean = text[event_search_end:]
                break
            else:
                text_clean = text
        else:
            text_clean = text
    
    return text_clean

def event_description_update(event, custom_flag, calendar_source, calendar_target, operation_timestamp, event_target=None, previous=constants.PREVIOUS, diff=constants.DIFF):
    watermark = {
        'calendar_source': calendar_source,
        'calendar_target': calendar_target,
        'id_source': event['id'],
        'updated_source': event['updated'],
        'operation_timestamp': operation_timestamp,
    }

    # Add `watermark` if there is any `recurringEventId`
    if 'recurringEventId' in event:
        watermark.update({'recurringEventId': event['recurringEventId']})

    # Create empty description
    if 'description' not in event:
        event['description'] = ""

    # To merge the `event_target` and the new `event_source` `description`
    if event_target:
        event_target_old = clean_previous(event_target['description'])
        event_diff = event_description_text_diff(event_target_old, event['description'])
        watermark_prev = f"<br><br>|{diff}|<br>{event_diff}<br>|/{diff}|<br><br>|{previous}|<br>{event_target['description']}"
    else:
        watermark_prev = ""

    #  Concatenate all key-values.
    watermark_s = ""
    for k,v in watermark.items():
        watermark_s = f"{watermark_s}<br>{k}: {v}"
    watermark_s = f"<html-blob>|{custom_flag.upper()}|{watermark_s}<br>|/{custom_flag.upper()}|<br><br>{event['description']}{watermark_prev}</html-blob>"

    return watermark_s

def event_attendees_update(event, calendar_target, calendar_source=confidential.CALENDAR_SOURCE, calendar_target_name=confidential.CALENDAR_TARGET_NAME):
    # Add `attendee` to be able to import
    if 'attendees' in event:

        # Copy the status from the source calendar
        response_status = 'accepted'  # Default value
        for attendee in event['attendees']:
            if set(['email', 'responseStatus']).issubset(attendee):
                if attendee['email'] == calendar_source:
                    response_status = attendee['responseStatus']

        self_attendee = {"email": calendar_target, "displayName": calendar_target_name, "self": True, "responseStatus": response_status}
        event['attendees'].append(self_attendee)
        
    else:
        self_attendee = {"email": calendar_target, "displayName": calendar_target_name, "self": True, "responseStatus": "accepted"}
        event['attendees'] = [self_attendee]
    
    return event['attendees']