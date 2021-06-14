import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
import requests
import json
from util import get_value

# slack stuff
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# user mentions (@s) app
@app.event("app_mention")
def update(client, event,logger):
    try:
        # monday stuff
        apiKey = os.environ.get("MONDAY_API_KEY")
        apiUrl = "https://api.monday.com/v2"
        headers = {"Authorization" : apiKey}
        board_id = "1029994357"
        query5 = 'mutation ($myItemName: String!, $columnVals: JSON!) { create_item (board_id:'+board_id+', item_name:$myItemName, column_values:$columnVals) { id } }'
        vars = {
        'myItemName' : event["blocks"][0]["elements"][0]["elements"][1]["text"],
        'columnVals' : json.dumps({
        'status_11' : {'label' : 'Frontend'},
        })
        }
        print(event["blocks"][0]["elements"][0]["elements"][1]["text"])
        
        
        data = {'query' : query5, 'variables' : vars}
        r = requests.post(url=apiUrl, json=data, headers=headers) # make request
        print(r.json())
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

# user clicks "File a bug" under Bolt icon
# The open_modal shortcut listens to a shortcut with the callback_id "open_modal"
@app.shortcut("file_bug")
def open_modal(ack, shortcut, client, logger, body):
    ack()

    with open('bug-file.json') as file:
        bug_file = json.load(file)
    try:
        # Call the views_open method using the built-in WebClient
        api_response = client.views_open(
            trigger_id=shortcut["trigger_id"],
            # View payload for a modal
            view=bug_file)
        logger.info(api_response)
        
    except SlackApiError as e:
        logger.error("Error creating conversation: {}".format(e))

# Open user submission of modal of callback_id "view-d"
@app.view("view-id")
def view_submission(ack, client, body, view, logger):
    ack()

    # get user submitted info
    user = body["user"]["name"]
    blocks = body["view"]["state"]["values"]

    site = get_value('site', 'site-action', blocks)
    description = get_value('bug-description', 'bug-description-action', blocks)
    visibility = int(get_value('visibility','visibility-action', blocks))
    impact = int(get_value('impact', 'impact-action', blocks))
    to_reproduce = get_value('how-to-reproduce', 'how-to-reproduce-action', blocks)
    expected = get_value('expected-behavior', 'expected-behavior-action', blocks)
    config = get_value('config', 'config-action', blocks)

    # create new monday item
    api_key = os.environ.get("MONDAY_API_KEY")
    board_id = os.environ.get("BOARD_ID")

    apiUrl = "https://api.monday.com/v2"
    headers = {"Authorization" : api_key}

    create_item = 'mutation ($myItemName: String!, $columnVals: JSON!) { create_item (board_id:'+board_id+', item_name:$myItemName, column_values:$columnVals) { id } }'
    vars = {
        'myItemName' : description,
        'columnVals' : json.dumps({
            'status_11' : {'label' : site},
            'numbers' : visibility,
            'numbers0' : impact
        })
    }
    new_item = {'query' : create_item, 'variables' : vars}
    r = requests.post(url=apiUrl, json=new_item, headers=headers) # make request
    r_json = r.json()
    print(r_json)
    item_id = r_json["data"]["create_item"]["id"] # save item id

    # create update within newly created item
    body = json.dumps("<p><strong>Description</strong></p>"+description+"<p><strong>Visibility</strong></p>"+str(visibility)+"<p><strong>Impact</strong></p>"+str(impact)+"<p><strong>To Reproduce</strong></p>"+to_reproduce+"<p><strong>Expected behavior</strong></p>"+expected+"<p><strong>Configuration</strong></p>"+config+"<p><strong>Filed by</strong></p>"+user)

    create_update = 'mutation { create_update (item_id:'+item_id+', body:'+body+') { id } }'
    new_update = {'query' : create_update}
    r = requests.post(url=apiUrl, json=new_update, headers=headers) # make request
    print(r.json())

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()