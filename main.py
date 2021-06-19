import os
import json
import re
import requests
import pandas as pd

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from helpers import monday
from helpers import util
from helpers.bug import Bug

# slack stuff
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# user uploads file to channel
@app.event(
    event={"type": "message", "subtype": "file_share"}
)
def get_image(ack, client, body, logger):
    ack()

    try:
        # collect image URL
        file_URL = body["event"]["files"][0]["url_private"]
        # collect ts for message to respond to 
        message_ts = body["event"]["event_ts"]

        # get last 5 submitted bug reports
        df = pd.read_csv('data/history.csv', sep=',',header=0, error_bad_lines=False)
        last_5 = df.tail(5)

        # create dropdown menu of last 5 submitted bug reports
        options = []
        for index in last_5.index:
            description = str(last_5['description'][index])
            item_id = str(last_5['monday_item_id'][index])
            options.append(
                            {
                            "text": {
                                "type": "plain_text",
                                "text": description
                            },
                            "value": item_id
                            })
        blocks = [
            {
                "type": "section",
                "block_id": "which_item",
                "text": {
                "type": "mrkdwn",
                "text": "You uploaded a <"+file_URL+"|file>, which monday item do you want to attach this to?"
                },
                "accessory": {
                "action_id": "item_select",
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an item"
                },
                "confirm": {
                    "title": {
                        "type": "plain_text",
                        "text": "Are you sure?"
                    },
                    "text": {
                        "type": "mrkdwn",
                        "text": "This will upload the image to the chosen monday item."
                    },
                    "confirm": {
                        "type": "plain_text",
                        "text": "Confirm"
                    },
                    "deny": {
                        "type": "plain_text",
                        "text": "Cancel"
                    }
                },
                "options": options
                },
            }
        ]
        client.chat_postMessage(
            channel = os.environ.get("SLACK_CHANNEL_ID"),
            text = "Error with blocks",
            blocks = blocks,
            thread_ts=message_ts
        )
    except KeyError as e:
        logger.error("No file uploaded: {}".format(e))

# user selects a monday item from dropdown
@app.action("item_select")
def upload_image(ack, client, body):
    ack()

    # grab info
    item_id = body["actions"][0]["selected_option"]["value"]
    text = body["message"]["blocks"][0]["text"]["text"]
    # grab image URL from text
    try:
        url = re.search('<(.*)\|', text).group(1)
    except AttributeError:
        url = ''

    # Download file
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

    # get item_id
    df = pd.read_csv('data/history.csv', sep=',',header=0, error_bad_lines=False)
    df.set_index('monday_item_id', inplace=True)
    update_id = str(df['monday_update_id'][int(item_id)])

    # get file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    f = dir_path+'/'+filename

    # Upload file to update on monday.com
    monday.add_file_to_update(update_id=update_id, file=f)

    # Upload file to column on monday.com
    monday.add_file_to_column(item_id=item_id, file=f)
    
    # Delete message
    channel = body["container"]["channel_id"]
    message_ts = body["container"]["message_ts"]
    client.chat_delete(
        channel=channel,
        ts = message_ts
    )
    
    # Delete locally saved file
    os.remove(f)

# user clicks "File a bug" under Bolt icon
@app.shortcut("file_bug")
def open_modal(ack, shortcut, client, logger):
    '''
    The open_modal shortcut listens to a shortcut with the callback_id "file_bug"
    '''
    ack()

    with open('helpers/bug-file.json') as file:
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

# open user submission
@app.view("view-id")
def view_submission(ack, client, body, logger):
    '''
    Open view of modal of callback_id "view-id"
    '''
    ack()
    try:
        bug = Bug()
        # who submitted?
        bug.user = body["user"]["username"]
        bug.name = body["user"]["name"]
        bug.user_id = body["user"]["id"]
        # digest info
        blocks = body["view"]["state"]["values"]
        bug.site = util.get_value('site', 'site-action', blocks)
        bug.description = util.get_value('bug-description', 'bug-description-action', blocks)
        bug.visibility = int(util.get_value('visibility','visibility-action', blocks))
        bug.visibility_text = util.get_text('visibility','visibility-action', blocks) #text
        bug.impact = int(util.get_value('impact', 'impact-action', blocks))
        bug.impact_text = util.get_text('impact', 'impact-action', blocks) # text
        bug.to_reproduce = util.get_value('how-to-reproduce', 'how-to-reproduce-action', blocks)
        bug.expected = util.get_value('expected-behavior', 'expected-behavior-action', blocks)
        bug.config = util.get_value('config', 'config-action', blocks)
    except (IndexError, KeyError, TypeError) as e:
        logger.error("Error, data has unexpected inner structure: {}".format(e))
    except SlackApiError as e:
        logger.error("Error retrieving view: {}".format(e))

    # create monday item + update
    monday.create_item(bug)
    monday.create_update(bug)

    # save submission 
    util.save_to_history(bug)

    # send message to #dev-bugs
    _send_summary(bug, client, logger)

# Send summary of user submitted bug report to slack channel
def _send_summary(bug, client, logger):
    try:
        # backup text
        text = "*Bug File* submission from <@"+bug.user_id+"> \n"+"\n*Site*\n"+bug.site+"\n\n*Describe the bug*\n"+bug.description+"\n\n*Visibility*\n"+str(bug.visibility)+"\n\n*Impact*\n"+str(bug.impact)+"\n\n*To Reproduce*\n"+bug.to_reproduce+"\n\n*Expected behavior*\n"+bug.expected+"\n\n*Configuration (e.g. browser type, screen size, device)*\n"+bug.config
        # format blocks
        blocks = [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Bug file submission from * <@"+bug.user_id+"> \n (see <"+bug.monday_item_url+"|here>)",
                        "verbatim": False
                    }
                    }, {
                        "type": "divider",
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Describe the bug* \n "+bug.description,
                            "verbatim": False
                        }
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Site* \n "+bug.site,
                            "verbatim": False
                        }
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Visibility* \n "+bug.visibility_text,
                            "verbatim": False
                        }
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Impact* \n "+bug.impact_text,
                            "verbatim": False
                        }
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*To Reproduce* \n "+bug.to_reproduce,
                            "verbatim": False
                        }
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Expected behavior* \n "+bug.expected,
                            "verbatim": False
                        }
                    }, {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Configuration (e.g. browser type, screen size, device)* \n"+bug.config,
                            "verbatim": False
                        }
                    }, {
                        "type": "divider"
                    }]
        # send message
        client.chat_postMessage(
            channel = os.environ.get("SLACK_CHANNEL_ID"),
            text = text,
            blocks = blocks
        )
    except (IndexError, KeyError, TypeError) as e:
        logger.error("Error sending channel message, data structures don't match: {}".format(e))
    except SlackApiError as e:
        logger.error("Error sending channel message, some slack issue: {}".format(e))

@app.event("message")
def ignore_message():
    # ignore messages
    pass

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()