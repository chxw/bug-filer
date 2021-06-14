import csv
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

def save_to_history(user, user_id, site, description, visibility, impact, expected, to_reproduce, config):
    with open('history.csv', 'a', newline='') as file:
        history = csv.writer(file, delimiter=',')
        row = [dt.now(), user, user_id, site, description, visibility, impact, expected, to_reproduce, config]
        history.writerow(row)
        file.close()