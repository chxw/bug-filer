import csv
import os
from datetime import datetime as dt
import requests
import pandas as pd

def get_value(block_id, action_id, blocks):
    try:
        value = blocks[block_id][action_id]['value']
    except KeyError:
        value = blocks[block_id][action_id]['selected_option']['value']
    return value if value != None else "N/A"

def get_text(block_id, action_id, blocks):
    try:
        return blocks[block_id][action_id]['selected_option']['text']['text']
    except KeyError:
        return "N/A"

def save_to_history(bug):
    with open('data/history.csv', 'a', newline='') as file:
        history = csv.writer(file, delimiter=',')
        row = [dt.now(), bug.user, bug.name, bug.user_id, bug.site, bug.description, bug.visibility, bug.impact, bug.expected, bug.to_reproduce, bug.config, bug.monday_item_id, bug.monday_update_id, bug.monday_item_url, bug.monday_update_url]
        print(row)
        history.writerow(row)
        file.close()
    
def get_from_history(column, column_value):
    df = pd.read_csv('data/history.csv', sep=',',header=0, error_bad_lines=False)
    df.set_index('monday_item_id', inplace=True)
    return df[column][column_value]

def download_file_from_URL(url):
    filename = url.split("/")[-1]
    headers = {'Authorization': 'Bearer '+os.environ["SLACK_BOT_TOKEN"]}
    with open(filename, 'wb') as handle:
        response = requests.get(url, headers=headers, stream=True)
        if not response.ok:
            print(response)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    return filename