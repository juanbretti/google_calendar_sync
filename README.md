# google_calendar_sync
Sync two **Google Calendar** using the *API* and *Python*.

I had created this *Python* app, because when you import event, guests and conference data for that event are not imported ([Reference](https://support.google.com/calendar/answer/37118)). This will create `\code\client_secrets.json`.

Additionally create a file `\code\personal.py`, containing:
```python
CALENDAR_SOURCE = 'calendar_a@gmail.com'
CALENDAR_TARGET = 'calendar_b@gmail.com'
CALENDAR_TARGET_NAME = 'Your name'
PATH_DATA = "data"
```

Also a folder for the outputs to be stored at `\data\`.

Two personal files are required to authenticate to *Google*:
1. `\code\client_secrets.json`
2. `\calendar.dat`

## Create Google Calendar API private keys
To start syncing with Google Calendar, you’ll need to collect the Client ID and Client Secret from your Google API.\
Follow this [tutorial](https://simplyscheduleappointments.com/guides/google-api-credentials/).

# References
### Google Calendar API
Google Calendar API examples\
https://github.com/googleapis/google-api-python-client/tree/main/samples/calendar_api

Google Calendar API reference guide\
https://developers.google.com/calendar/api/v3/reference/events

### Google Cloud Console
Check Google API quota\
https://console.cloud.google.com/apis/api/calendar-json.googleapis.com/quotas?authuser=1&project=skilful-charmer-357720

Check Google APIs created\
https://console.cloud.google.com/projectselector2/apis/dashboard

