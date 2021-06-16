import os
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from monday import create_item, create_update
from util import get_value, get_text, save_to_history
from bug import Bug

# slack stuff
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# user sends file in #dev-bugs
@app.event("message")
def upload_image(client, body, logger):
    if body["event"]["files"]:
        send_message(client, "You uploaded a file, which monday item do you want to attach this to?", logger)

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
        channel_id=os.environ.get("SLACK_CHANNEL_ID")
        client.chat_postMessage(
            channel= channel_id,
            type="mrkdwn",
            # Backup text
            text="*Bug File* submission from <@"+bug.user_id+"> \n"+"\n*Site*\n"+bug.site+"\n\n*Describe the bug*\n"+bug.description+"\n\n*Visibility*\n"+str(bug.visibility)+"\n\n*Impact*\n"+str(bug.impact)+"\n\n*To Reproduce*\n"+bug.to_reproduce+"\n\n*Expected behavior*\n"+bug.expected+"\n\n*Configuration (e.g. browser type, screen size, device)*\n"+bug.config, 
            # Blocks
            # json.dumps() for parsing special unicode characters
            blocks=json.dumps([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Bug file submission from * <@"+bug.user_id+"> \n (see <"+bug.monday_update_url+"|here>)"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Item ID* \n"+bug.monday_item_id
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Describe the bug* \n"+bug.description
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Site* \n"+bug.site
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Visibility* \n"+bug.visibility_text
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Impact* \n"+bug.impact_text
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*To Reproduce* \n"+bug.to_reproduce
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Expected behavior* \n"+bug.expected
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Configuration (e.g. browser type, screen size, device)* \n"+bug.config
                    }
                },
                {
                    "type": "divider"
                }
            ])
        )
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

@app.command("/add")
def add_update(ack, body):
    ack()
    print(body)


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()