import os
import pandas as pd
from datetime import datetime as dt

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from helpers import monday
from helpers import util
from helpers.bug import Bug

# Slack Bolt app
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Output to file
output = open('data/output.txt', 'a')
output.write(str(dt.now())+': \n')


def _add_image_to_monday(url, item_id, **kwargs):
    """
    Upload image (url) to monday item's update (update_id) and in "Files" column (item_id).

    Keyword arguments:
    url -- image_url (i.e. https://...png).
    item_id -- id assigned to items by monday.com.
    update_id -- id assigned to updates by monday.com.

    Monday API supports PNG, JPEG, Word, PDF, Excel, GIF, MP4, SVG, TXT, AI formats.
    """
    # Download private slack file
    filename = util.download_file_from_URL(url)

    # get update_id
    if 'update_id' in kwargs:
        update_id = kwargs.get('update_id')
    else:
        try:
            update_id = str(util.get_from_history(
                'monday_update_id', int(item_id)))
        except KeyError as e:
            output.write("Row in history.csv not found: {}".format(e))
        except ValueError as e:
            update_id = str(util.get_from_history(
                'monday_update_id', int(float(item_id))))

    # catch string ending in .0
    update_id = int((float(update_id)))
    item_id = int((float(item_id)))

    # get file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    f = dir_path+'/'+filename

    # Upload file to update on monday.com
    monday.add_file_to_update(update_id=update_id, file=f)

    # Upload file to column on monday.com
    monday.add_file_to_column(item_id=item_id, file=f)

    # Delete locally saved file
    os.remove(f)


# SHARE FILE: File uploaded to channel (SLACK_CHANNEL_ID in .env)
@app.event(
    event={"type": "message", "subtype": "file_share"}
)
def handle_file_share(ack, client, body):
    """
    React to user's file share in SLACK_CHANNEL_ID. Grab all url_private items and use to upload to existing monday item or to upload with a new monday item.
    """
    ack()

    try:

        # collect image
        file_urls = []
        for file in body["event"]["files"]:
            file_urls.append(file["url_private"])
        # collect ts for file upload message
        message_ts = body["event"]["event_ts"]

        # get last 5 submitted bug reports
        df = pd.read_csv('data/history.csv', sep=',',
                         header=0, error_bad_lines=False)
        last_5 = df.tail(5)

        # create 'options' list of last 5 reports for dropdown menu
        options = []
        for index in last_5.index:
            description = str(last_5['description'][index])
            item_id = str(last_5['monday_item_id'][index])
            # truncate
            description = description[:20] + \
                '..' if len(description) > 20 else description
            options.append(
                {
                    "text": {
                        "type": "plain_text",
                        "text": description.strip()
                    },
                    "value": item_id
                })

        # create Slack blocks
        blocks = [
            {
                "type": "section",
                "block_id": "which_item",
                "text": {
                    "type": "mrkdwn",
                    "text": "You uploaded a file, which monday item do you want to attach this to?"
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
                    "value": ' '.join(file_urls),
                    "action_id": "create_item"
                }
            }
        ]

        # Reply in thread to file upload message
        client.chat_postMessage(
            channel=os.environ.get("SLACK_CHANNEL_ID"),
            text="You uploaded a file, which monday item do you want to attach this to?",
            blocks=blocks,
            thread_ts=message_ts
        )
    except KeyError as e:
        output.write("No file uploaded: {}".format(e))


@app.action("item_select")
def image_select(ack, client, body):
    """
    Get which dropdown item (representation of monday) user selected and upload file to the corresponding monday item. 
    """
    ack()

    # grab info
    item_id = body["actions"][0]["selected_option"]["value"]
    file_urls = body["message"]["blocks"][1]["accessory"]["value"]

    file_urls = file_urls.split()

    for url in file_urls:
        _add_image_to_monday(url, item_id)

    # Delete message
    client.chat_delete(
        channel=body["container"]["channel_id"],
        ts=body["container"]["message_ts"]
    )


# MESSAGE SHORTCUT: user clicks "Create Item" in image attachment message
@app.action("create_item")
def file_bug_with_image(ack, client, body):
    """
    Create new monday item with uploaded images. 
    """
    ack()

    file_urls = []
    for file in body["actions"]:
        file_urls.append(file["value"])

    trigger_id = body["trigger_id"]

    _open_modal(ack=ack, trigger_id=trigger_id,
                client=client, file_urls=file_urls)

    # Delete message
    client.chat_delete(
        channel=body["container"]["channel_id"],
        ts=body["container"]["message_ts"]
    )


# GLOBAL SHORTCUT: user clicks "Create Item" in global shortcut
@app.shortcut("file_bug")
def file_bug(ack, shortcut, body, client):
    """
    The open_modal shortcut listens to a shortcut with the callback_id "file_bug"
    """
    ack()

    trigger_id = shortcut["trigger_id"]

    try:
        # future feature, extract text from message and auto-fill bug file
        # text = body["message"]["text"]
        file_urls = []
        for file in body["message"]["files"]:
            file_urls.append(file["url_private"])
    except KeyError:
        pass

    _open_modal(ack, trigger_id, client, file_urls=file_urls)


def _open_modal(ack, trigger_id, client, **kwargs):
    """
    Open Slack modal (form) for user to fill out bug report. Include urls of files in private_metadata if file_urls included in args. 
    """

    ack()

    file_urls = kwargs.get('file_urls', [])

    # with open('helpers/bug-file.json') as file:
    #     bug_file = json.load(file)

    bug_file = {
        "type": "modal",
        "callback_id": "bug_file",
        "private_metadata": ' '.join(file_urls),
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
                "block_id": "site",
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
                "block_id": "bug-description",
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
                "block_id": "visibility",
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
                "block_id": "impact",
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
                "block_id": "how-to-reproduce",
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
                "block_id": "expected-behavior",
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
                "block_id": "config",
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
        api_response = client.views_open(
            trigger_id=trigger_id,
            # View payload for a modal
            view=bug_file)
        output.write(str(api_response))

    except SlackApiError as e:
        output.write("Error creating conversation: {}".format(e))


# When user saves Slack modal
@app.view("bug_file")
def view_submission(ack, client, body):
    """
    Open user submission (view of modal of callback_id "view-id")
    """
    ack()

    bug = Bug()

    file_upload = False

    # check if this is a file upload
    if body["view"]["private_metadata"] != '':
        file_upload = True

    try:
        # if file upload, grab
        if file_upload:
            bug.file_urls = body["view"]["private_metadata"].split()
        # who submitted?
        bug.user = body["user"]["username"]
        bug.name = body["user"]["name"]
        bug.user_id = body["user"]["id"]
        # grab form values
        blocks = body["view"]["state"]["values"]
        # fill out monday columns
        bug.site = util.get_value('site', 'site-action', blocks)
        bug.description = util.get_value(
            'bug-description', 'bug-description-action', blocks)
        bug.visibility = int(util.get_value(
            'visibility', 'visibility-action', blocks))
        bug.visibility_text = util.get_text(
            'visibility', 'visibility-action', blocks)  # text
        bug.impact = int(util.get_value('impact', 'impact-action', blocks))
        bug.impact_text = util.get_text(
            'impact', 'impact-action', blocks)  # text
        bug.to_reproduce = util.get_value(
            'how-to-reproduce', 'how-to-reproduce-action', blocks)
        bug.expected = util.get_value(
            'expected-behavior', 'expected-behavior-action', blocks)
        bug.config = util.get_value('config', 'config-action', blocks)
    except (IndexError, KeyError, TypeError) as e:
        output.write(
            "Error, data has unexpected inner structure: {}".format(e))
    except SlackApiError as e:
        output.write("Error retrieving view: {}".format(e))

    # create monday item + update
    monday.create_item(bug)
    monday.create_update(bug)

    # add file to monday
    if file_upload:
        for file_url in bug.file_urls:
            _add_image_to_monday(
                url=file_url, item_id=bug.monday_item_id, update_id=bug.monday_update_id)

    # save submission
    util.save_to_history(bug)

    # send message to #dev-bugs
    _send_summary(bug, client)


def _send_summary(bug, client):
    """
    Send summary of user submitted bug report to SLACK_CHANNEL_ID.
    """
    try:
        # backup text
        text = "*Bug File* submission from <@"+bug.user_id+"> \n"+"\n*Site*\n"+bug.site+"\n\n*Describe the bug*\n"+bug.description+"\n\n*Visibility*\n"+str(bug.visibility)+"\n\n*Impact*\n"+str(
            bug.impact)+"\n\n*To Reproduce*\n"+bug.to_reproduce+"\n\n*Expected behavior*\n"+bug.expected+"\n\n*Configuration (e.g. browser type, screen size, device)*\n"+bug.config
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
        # send summary message
        client.chat_postMessage(
            channel=os.environ.get("SLACK_CHANNEL_ID"),
            text=text,
            blocks=blocks
        )
    except (IndexError, KeyError, TypeError) as e:
        output.write(
            "Error sending channel message, data structures don't match: {}".format(e))
    except SlackApiError as e:
        output.write(
            "Error sending channel message, some slack issue: {}".format(e))


@app.event("message")
def ignore_message():
    """
    Ignore irrelevant messages in SLACK_CHANNEL_ID. 
    """
    pass


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
