import os
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from monday import create_item, create_update
from util import get_value, get_text, save_to_history

# slack stuff
app = App(token=os.environ["SLACK_BOT_TOKEN"])

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

    try:
        # get submitted info
        user = body["user"]["username"]
        name = body["user"]["name"]
        user_id = body["user"]["id"]
        blocks = body["view"]["state"]["values"]
    
    except SlackApiError as e:
        logger.error("Error retrieving view: {}".format(e))

    # digest info
    site = get_value('site', 'site-action', blocks)
    description = get_value('bug-description', 'bug-description-action', blocks)
    visibility = int(get_value('visibility','visibility-action', blocks))
    visibility_text = get_text('visibility','visibility-action', blocks) #text
    impact = int(get_value('impact', 'impact-action', blocks))
    impact_text = get_text('impact', 'impact-action', blocks) # text
    to_reproduce = get_value('how-to-reproduce', 'how-to-reproduce-action', blocks)
    expected = get_value('expected-behavior', 'expected-behavior-action', blocks)
    config = get_value('config', 'config-action', blocks)

    # create monday item
    monday_item_id = create_item(site, description, visibility, impact)
    # create monday url
    monday_update_url = create_update(name, description, visibility_text, impact_text, to_reproduce, expected, config, monday_item_id)

    # save submission
    save_to_history(user, name, user_id, site, description, visibility, impact, expected, to_reproduce, config, monday_item_id, monday_update_url)

    # send message to channel
    channel_id=os.environ.get("SLACK_CHANNEL_ID")
    client.chat_postMessage(
        channel= channel_id,
        type="mrkdwn",
        text="*Bug File* submission from <@"+user_id+"> \n"+"\n*Site*\n"+site+"\n\n*Describe the bug*\n"+description+"\n\n*Visibility*\n"+str(visibility)+"\n\n*Impact*\n"+str(impact)+"\n\n*To Reproduce*\n"+to_reproduce+"\n\n*Expected behavior*\n"+expected+"\n\n*Configuration (e.g. browser type, screen size, device)*\n"+config, 
        # json.dumps() necessary for for parsing special unicode characters
        blocks=json.dumps([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Bug file submission from * <@"+user_id+"> (see <"+monday_update_url+"|here>)"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Describe the bug* \n"+description
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Site* \n"+site
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Visibility* \n"+visibility_text
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Impact* \n"+impact_text
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*To Reproduce* \n"+to_reproduce
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Expected behavior* \n"+expected
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Configuration (e.g. browser type, screen size, device)* \n"+config
                }
            },
            {
                "type": "divider"
            }
        ])
    )

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()