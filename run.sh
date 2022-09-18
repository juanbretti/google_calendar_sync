#!/bin/bash

# First run, to install apps
# apt-get update && apt-get upgrade
# apt-get install -y cron
# apt-get install -y nano
# pip install -r /usr/src/app/requirements.txt --user

# Run all the time
service cron start
bash