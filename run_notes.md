## Docker name
google_calendar_sync
sh /usr/src/app/run.sh
/usr/src/app

# First run, to prepare the Docker container
Disable the `First run, to install apps`

# Edit the cron job
crontab -e
0 * * * * cd /usr/src/app && /usr/local/bin/python /usr/src/app/code/main.py >> /usr/src/app/crontab_run.log

# Reference
## Install missing applications in Linux
apt-get update && apt-get upgrade
apt-get install -y cron
apt-get install -y nano

## Create the cron
https://towardsdatascience.com/how-to-schedule-python-scripts-with-cron-the-only-guide-youll-ever-need-deea2df63b4e
https://linuxhint.com/check_working_crontab/
https://crontab-generator.org/

crontab -e
0 * * * * cd /usr/src/app && /usr/local/bin/python /usr/src/app/code/main.py >> /usr/src/app/crontab_run.log
service cron start
service cron status

## Manual run, if needed
cd /usr/src/app
pip install -r requirements.txt --user
python code/main.py
