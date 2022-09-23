# google_calendar_sync
Sync two **Google Calendar** using the *API* and *Python*.

I had created this *Python* app, because when you import event, guests and conference data for that event are not imported ([Reference](https://support.google.com/calendar/answer/37118)).

To use this application, you need to create:
A file `\code\confidential.py`, containing:
```python
CALENDAR_SOURCE = 'user_a@gmail.com'
CALENDAR_TARGET = 'user_a@your_domain.com'
CALENDAR_TARGET_NAME = "Your name"
PATH_DATA = "data"
URL_GOOGLE_WORKSPACE = "https://calendar.google.com/a/your_domain.com"

SMTP_USERNAME = 'user_a@your_domain.com'
SMTP_PASSWORD = 'your_secure_password'
SMTP_SERVER = 'smtp.your_domain.com'
SMTP_PORT = 465
RECEIVER_NAME = CALENDAR_TARGET_NAME
RECEIVER_MAIL = 'user_a+google_calendar_sync@your_domain.com'
```

A folder for the outputs to be stored at `\data`.

Two personal files are required to authenticate to *Google*:
1. `\code\client_secrets.json`. Bellow a tutorial.
2. `\calendar.dat`. This is automatically created after the first execution of the application.

Two ways to execute:
1. Run `main.py`. Recommended.
2. Run `calendar_move_import_operations.py`. This is an old version of the code.

## Create Google Calendar API private keys
To start syncing with Google Calendar, you’ll need to collect the Client ID and Client Secret from your Google API.\
Follow this [tutorial](https://simplyscheduleappointments.com/guides/google-api-credentials/). This will create `\code\client_secrets.json`.

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

### Send emails using Python
Tutorial\
https://realpython.com/python-send-email/#sending-fancy-emails