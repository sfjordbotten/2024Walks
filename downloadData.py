import requests
import datetime
import pandas as pd
import os
import re
import win32api
import time

# downloads folder default
downloadFolder = r'C:\Users\scott\Downloads'

# # file with lifetime data - This is up to 2-Nov-2024
# lifetimeDataFile = "user41688257_workout_history.csv"

# file with lifetime data - 3-Nov-2024 to 27-Dec-2024
lifetimeDataFile = "user41688257_workout_history_2024-12-28.csv"
# year to download
year = 2024

# load data from csv
summary = pd.read_csv(lifetimeDataFile)

# if data folder does not exist, make it
if not os.path.isdir('data'):
    os.mkdir('data')
if not os.path.isdir(os.path.join('data', str(year))):
    os.mkdir(os.path.join('data', str(year)))

# specify path for downloading data
downloadPath = os.path.join('data', str(year))

# loop through rows and download data
count = 0
for iii in range(0, len(summary)):
    if '2024' in summary['Workout Date'][iii]:
        # download file
        win32api.ShellExecute(None,
                              'open',
                              summary['Link'][iii].replace('/workout', '/workout/export') + '/tcx',
                              None,
                              '.',
                              0)
        count += 1
        time.sleep(1)

# look for downloaded files of expected format and move
moved = 0
while moved < count:
    files = os.listdir(downloadFolder)
    for file in files:
        if os.path.splitext(file)[1] == '.tcx':
            if datetime.datetime.fromtimestamp(os.path.getctime(os.path.join(downloadFolder, file))).date() == datetime.datetime.now().date():
                os.replace(os.path.join(downloadFolder, file), os.path.join(downloadPath, file))
                moved += 1