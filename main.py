import os
import json
import re
import requests
import pandas as pd

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from slackblocks import Message, SectionBlock, DividerBlock

from monday import add_file_to_update, create_item, create_update
from util import get_value, get_text, save_to_history
from bug import Bug

# Import smtplib for the actual sending function
import smtplib

# And imghdr to find the types of our images
import imghdr

# Here are the email package modules we'll need
from email.message import EmailMessage


# slack stuff
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# user uploads file to channel
@app.event(
    event={"type": "message", "subtype": re.compile("(me_message)|(file_share)")}
)
def get_image(ack, client, body, logger):
    ack()
    try:
        file_URL = body["event"]["files"][0]["url_private"]
        # reply to thread
        message_ts = body["event"]["event_ts"]

        # get last 5 submitted bug reports
        df = pd.read_csv('history.csv', sep=',',header=0, error_bad_lines=False)
        last_5 = df.tail(5)
        options = []
        for index in last_5.index:
            text = str(last_5['description'][index])
            value = str(last_5['monday_update_id'][index])
            options.append(
                            {
                            "text": {
                                "type": "plain_text",
                                "text": text
                            },
                            "value": value
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

@app.action("item_select")
def upload_image(ack, client, body, logger):
    ack()

    # grab info
    update_id = body["actions"][0]["selected_option"]["value"]
    text = body["message"]["blocks"][0]["text"]["text"]
    try:
        url = re.search('<(.*)\|', text).group(1)
    except AttributeError:
        #url not found
        url = '' # apply your error handling
    print(url)

    ## Download file
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

    # Upload file to monday.com
    add_file_to_update(update_id=update_id)
    
    # Delete message
    channel = body["container"]["channel_id"]
    message_ts = body["container"]["message_ts"]
    client.chat_delete(
        channel=channel,
        ts = message_ts
    )

# user clicks "File a bug" under Bolt icon
@app.shortcut("file_bug")
def open_modal(ack, shortcut, client, logger):
    '''
    The open_modal shortcut listens to a shortcut with the callback_id "file_bug"
    '''
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
        bug.site = get_value('site', 'site-action', blocks)
        bug.description = get_value('bug-description', 'bug-description-action', blocks)
        bug.visibility = int(get_value('visibility','visibility-action', blocks))
        bug.visibility_text = get_text('visibility','visibility-action', blocks) #text
        bug.impact = int(get_value('impact', 'impact-action', blocks))
        bug.impact_text = get_text('impact', 'impact-action', blocks) # text
        bug.to_reproduce = get_value('how-to-reproduce', 'how-to-reproduce-action', blocks)
        bug.expected = get_value('expected-behavior', 'expected-behavior-action', blocks)
        bug.config = get_value('config', 'config-action', blocks)
    except (IndexError, KeyError, TypeError) as e:
        logger.error("Error, data has unexpected inner structure: {}".format(e))
    except SlackApiError as e:
        logger.error("Error retrieving view: {}".format(e))

    # create monday item + update
    create_item(bug)
    create_update(bug)

    # save submission 
    save_to_history(bug)

    # send message to #dev-bugs
    send_summary(bug, client, logger)

# Send summary of user submitted bug report to slack channel
def send_summary(bug, client, logger):
    try:
        # backup text
        text = "*Bug File* submission from <@"+bug.user_id+"> \n"+"\n*Site*\n"+bug.site+"\n\n*Describe the bug*\n"+bug.description+"\n\n*Visibility*\n"+str(bug.visibility)+"\n\n*Impact*\n"+str(bug.impact)+"\n\n*To Reproduce*\n"+bug.to_reproduce+"\n\n*Expected behavior*\n"+bug.expected+"\n\n*Configuration (e.g. browser type, screen size, device)*\n"+bug.config
        # format blocks
        title = SectionBlock("*Bug file submission from * <@"+bug.user_id+"> \n (see <"+bug.monday_item_url+"|here>)")
        item_id = SectionBlock("*Item ID* \n"+bug.monday_item_id)
        description = SectionBlock("*Describe the bug* \n"+bug.description)
        site = SectionBlock("*Site* \n"+bug.site)
        visibility = SectionBlock("*Visibility* \n"+bug.visibility_text)
        impact = SectionBlock("*Impact* \n"+bug.impact_text)
        to_reproduce = SectionBlock( "*To Reproduce* \n"+bug.to_reproduce)
        expected = SectionBlock("*Expected behavior* \n"+bug.expected)
        config = SectionBlock("*Configuration (e.g. browser type, screen size, device)* \n"+bug.config)
        blocks = [title, DividerBlock(), item_id, description, site, visibility, impact, to_reproduce, expected, config, DividerBlock()]
        message = Message(channel="#test", text=text, blocks=blocks)
        client.chat_postMessage(**message) # send message
    except (IndexError, KeyError, TypeError) as e:
        logger.error("Error sending channel message, data structures don't match: {}".format(e))
    except SlackApiError as e:
        logger.error("Error sending channel message, some slack issue: {}".format(e))
    
def send_message(client, text, logger):
    try:
        channel_id=os.environ.get("SLACK_CHANNEL_ID")
        client.chat_postMessage(
            channel= channel_id,
            type="mrkdwn",
            text=text)
    except (IndexError, KeyError, TypeError) as e:
        logger.error("Error sending channel message, data structures don't match: {}".format(e))
    except SlackApiError as e:
        logger.error("Error sending channel message, some slack issue: {}".format(e))

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()