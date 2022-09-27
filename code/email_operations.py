#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://realpython.com/python-send-email/#sending-fancy-emails

import datetime
from zoneinfo import ZoneInfo

import confidential
import constants

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(events_df_execution, events_counter, calendar_source, calendar_target, execution_timestamp, time_range=None, updated_min=None):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Google Calendar Sync summary"
    message["From"] = f'Python App <{confidential.SMTP_USERNAME}>'
    message["To"] = f'{confidential.RECEIVER_NAME} <{confidential.RECEIVER_MAIL}>'

    # Create the plain-text and HTML version of your message
    text =  ', '.join(f'{k}: {v}' for k, v in events_counter.items())
    
    html = """<html>
        <head>
            <style>
                table, th, td {
                    border: 1px solid black;
                    border-collapse: collapse;
                    }
            </style>
        </head>
        <body>"""
    html = html + "<h1>Summary</h1>"
    execution_timestamp_formatted = datetime.datetime.fromisoformat(execution_timestamp[:-1]).astimezone(ZoneInfo(constants.TIME_ZONE)).strftime(constants.DATE_FORMAT)
    html = html + f"<b>calendar_source</b>: {calendar_source}<br><b>calendar_target</b>: {calendar_target}<br><b>execution_timestamp_formatted</b>: {execution_timestamp_formatted}"
    if time_range is not None:
        html = html + f"<br><b>time_range</b>: {time_range}"
    if updated_min is not None:
        updated_min_formatted = datetime.datetime.fromisoformat(updated_min[:-1]).astimezone(ZoneInfo(constants.TIME_ZONE)).strftime(constants.DATE_FORMAT)
        html = html + f"<br><b>updated_min_formatted</b>: {updated_min_formatted}"
    
    html = html + "<br><br><h1>Counters</h1>"
    for k, v in events_counter.items():
        if v > 0:
            html = html + f'<b>{k}</b>: {v}<br>'
    html = html + "<br><h1>Events</h1>"
    html = html + """<table>
        <tr>
            <td><b>id_source</b></td>
            <td><b>inserted_target</b></td>
            <td><b>summary_source</b></td>
            <td><b>link</b></td>
        </tr>"""

    for index, row in events_df_execution.iterrows():

        html = html + f"""
            <tr>
                <td>{row['id_source']}</td>
                <td>{row['inserted_target']}</td>
                <td>{row['summary_source']}</td>
                <td><a href='{confidential.URL_GOOGLE_WORKSPACE}/r/search?q={row['id_source']}'>Search</a></td>
            </tr>"""
    
    html = html + "</table></body></html>"

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(confidential.SMTP_SERVER, confidential.SMTP_PORT, context=context) as server:
        server.login(confidential.SMTP_USERNAME, confidential.SMTP_PASSWORD)
        server.sendmail(confidential.SMTP_USERNAME, confidential.RECEIVER_MAIL, message.as_string())

    if constants.LOG_PRINT:
        print(f"Email sent with {events_counter['global']} events")