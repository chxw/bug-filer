import os
# import json
import re
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
def get_image(ack, client, body):
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
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Or you can create a new item:"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Create Item",
                        "emoji": True
                    },
                    "value": file_URL,
                    "action_id": "create_item"
                }
            }
        ]
        client.chat_postMessage(
            channel = os.environ.get("SLACK_CHANNEL_ID"),
            text = "Error with blocks",
            blocks = blocks,
            thread_ts=message_ts
        )
    except KeyError as e:
        print("No file uploaded: {}".format(e))

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

    add_image_to_monday(url, item_id)
    
    # Delete message
    client.chat_delete(
        channel=body["container"]["channel_id"],
        ts = body["container"]["message_ts"]
    )

def add_image_to_monday(url, item_id, **kwargs):
    # Download private slack file
    filename = util.download_file_from_URL(url)

    # get update_id
    if 'update_id' in kwargs:
        update_id = kwargs.get('update_id')
    else:
        try:
            update_id = str(util.get_from_history('monday_update_id', int(item_id)))
        except KeyError as e:
            print("Row in history.csv not found: {}".format(e))

    # get file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    f = dir_path+'/'+filename

    # Upload file to update on monday.com
    monday.add_file_to_update(update_id=update_id, file=f)

    # Upload file to column on monday.com
    monday.add_file_to_column(item_id=item_id, file=f)
    
    # Delete locally saved file
    os.remove(f)

# user clicks "Create Item" in image attachment message
@app.action("create_item")
def file_bug_with_image(ack, client, body):
    ack()

    file_URL = body["actions"][0]["value"]
    trigger_id = body["trigger_id"]

    file_bug(trigger_id, client, file_URL=file_URL)

    # Delete message
    client.chat_delete(
        channel=body["container"]["channel_id"],
        ts = body["container"]["message_ts"]
    )

# user uses "file_bug" shortcut
@app.shortcut("file_bug")
def open_modal(ack, shortcut, body, client):
    '''
    The open_modal shortcut listens to a shortcut with the callback_id "file_bug"
    '''
    ack()

    trigger_id = shortcut["trigger_id"]
    file_URL = None

    try: 
        ## future feature, extract text from message and auto-fill bug file
        # text = body["message"]["text"]
        file_URL = body["message"]["files"][0]["url_private"]
    except KeyError as e:
        print("Error accessing file from shortcut: {}".format(e))

    file_bug(trigger_id, client, file_URL=file_URL)

def file_bug(trigger_id, client, **kwargs):
    file_URL = kwargs.get('file_URL', None)

    # with open('helpers/bug-file.json') as file:
    #     bug_file = json.load(file)

    bug_file = {
                    "type": "modal",
                    "callback_id": "view-id",
                    "private_metadata": file_URL,
                    "title": {
                        "type": "plain_text",
                        "text": "File a bug",
                        "emoji": True
                    },
                    "submit": {
                        "type": "plain_text",
                        "text": "Submit",
                        "emoji": True
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel",
                        "emoji": True
                    },
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": "This form will submit your bug to the #dev-bugs board on monday.com",
                                "emoji": True
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "input",
                            "block_id":"site",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Select site",
                                    "emoji": True
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "multidocs",
                                            "emoji": True
                                        },
                                        "value": "Multidocs"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "platform",
                                            "emoji": True
                                        },
                                        "value": "Platform"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "both",
                                            "emoji": True
                                        },
                                        "value": "Both"
                                    }
                                ],
                                "action_id": "site-action"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "Site",
                                "emoji": True
                            }
                        },
                        {
                            "type": "input",
                            "block_id":"bug-description",
                            "label": {
                                "type": "plain_text",
                                "text": "Describe the bug",
                                "emoji": True
                            },
                            "element": {
                                "type": "plain_text_input",
                                "multiline": True,
                                "action_id": "bug-description-action"
                            }
                        },
                        {
                            "type": "input",
                            "block_id":"visibility",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Rate visibility",
                                    "emoji": True
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "1️⃣ (login/signup, docs - getting started, access key management)",
                                            "emoji": True
                                        },
                                        "value": "1"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "2️⃣ clicks away",
                                            "emoji": True
                                        },
                                        "value": "2"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "3️⃣ clicks away",
                                            "emoji": True
                                        },
                                        "value": "3"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "4️⃣ clicks away",
                                            "emoji": True
                                        },
                                        "value": "4"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "5️⃣ clicks away",
                                            "emoji": True
                                        },
                                        "value": "5"
                                    }
                                ],
                                "action_id": "visibility-action"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "Visibility",
                                "emoji": True
                            }
                        },
                        {
                            "type": "input",
                            "block_id":"impact",
                            "element": {
                                "type": "static_select",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Rate impact",
                                    "emoji": True
                                },
                                "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "5️⃣ = Huge (angry, pain, crying, $10^5 ARR)",
                                            "emoji": True
                                        },
                                        "value": "5"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "4️⃣ = Large (anger, dismay, swearing, $10^4 ARR)",
                                            "emoji": True
                                        },
                                        "value": "4"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "3️⃣ = Big (frustration, annoyance, $10^3 ARR)",
                                            "emoji": True
                                        },
                                        "value": "3"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "2️⃣ = Medium (eye-rolling, $10^2 ARR)",
                                            "emoji": True
                                        },
                                        "value": "2"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "1️⃣ = Small (may make you laugh instead of cry, $10^1 ARR)",
                                            "emoji": True
                                        },
                                        "value": "1"
                                    }
                                ],
                                "action_id": "impact-action"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "Impact",
                                "emoji": True
                            }
                        },
                        {
                            "type": "input",
                            "block_id":"how-to-reproduce",
                            "label": {
                                "type": "plain_text",
                                "text": "To Reproduce",
                                "emoji": True
                            },
                            "element": {
                                "type": "plain_text_input",
                                "multiline": True,
                                "action_id": "how-to-reproduce-action"
                            }
                        },
                        {
                            "type": "input",
                            "block_id":"expected-behavior",
                            "label": {
                                "type": "plain_text",
                                "text": "Expected behavior",
                                "emoji": True
                            },
                            "element": {
                                "type": "plain_text_input",
                                "multiline": True,
                                "action_id": "expected-behavior-action"
                            },
                            "optional": True
                        },
                        {
                            "type": "input",
                            "block_id":"config",
                            "label": {
                                "type": "plain_text",
                                "text": "Configuration (e.g. browser type, screen size, device)",
                                "emoji": True
                            },
                            "element": {
                                "type": "plain_text_input",
                                "multiline": False,
                                "action_id": "config-action"
                            },
                            "optional": True
                        }
                    ]
                }

    try:
        # Call the views_open method using the built-in WebClient
        client.views_open(
            trigger_id=trigger_id,
            # View payload for a modal
            view=bug_file)
        
    except SlackApiError as e:
        print("Error creating conversation: {}".format(e))

# open user submission
@app.view("view-id")
def view_submission(ack, client, body):
    '''
    Open view of modal of callback_id "view-id"
    '''
    ack()

    bug = Bug()

    if body["view"]["private_metadata"] != '':
        file_upload = True

    try:
        # if file upload, grab URL
        if file_upload:
            bug.file_URL = body["view"]["private_metadata"]
        # who submitted?
        bug.user = body["user"]["username"]
        bug.name = body["user"]["name"]
        bug.user_id = body["user"]["id"]
        # digest info
        blocks = body["view"]["state"]["values"]
        # fill out bug info
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
        print("Error, data has unexpected inner structure: {}".format(e))
    except SlackApiError as e:
        print("Error retrieving view: {}".format(e))

    # create monday item + update
    monday.create_item(bug)
    monday.create_update(bug)

    # add file to monday
    if file_upload:
        add_image_to_monday(url=bug.file_URL, item_id=bug.monday_item_id, update_id=bug.monday_update_id)

    # save submission 
    util.save_to_history(bug)

    # send message to #dev-bugs
    _send_summary(bug, client)

# Send summary of user submitted bug report to slack channel
def _send_summary(bug, client):
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
        print("Error sending channel message, data structures don't match: {}".format(e))
    except SlackApiError as e:
        print("Error sending channel message, some slack issue: {}".format(e))

@app.event("message")
def ignore_message():
    # ignore messages
    pass

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()