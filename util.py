import csv
import pandas as pd
from datetime import datetime as dt

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

def get_last_5_submits():
    # history = open("history.csv", "r")
    # lines = history.readlines()
    # last_lines = lines[-5:]
    # print(last_lines)
    df=pd.read_csv('history.csv', sep=',',header=0)
    last_5 = df.tail(5)
    print(last_5.values)

def save_to_history(bug):
    with open('history.csv', 'a', newline='') as file:
        history = csv.writer(file, delimiter=',')
        row = [dt.now(), bug.user, bug.name, bug.user_id, bug.site, bug.description, bug.visibility, bug.impact, bug.expected, bug.to_reproduce, bug.config, bug.monday_item_id, bug.monday_update_id, bug.monday_item_url, bug.monday_update_url]
        history.writerow(row)
        file.close()