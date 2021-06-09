from logging import setLoggerClass
import os
from slack_bolt import App
from slack_sdk.errors import SlackApiError
import requests
import json
from bug import Bug
from util import get_value, get_text

# slack stuff
# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

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
        # print(event["blocks"]["elements"]["elements"])
        
        
        data = {'query' : query5, 'variables' : vars}
        r = requests.post(url=apiUrl, json=data, headers=headers) # make request
        print(r.json())
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

# The open_modal shortcut listens to a shortcut with the callback_id "open_modal"
@app.shortcut("file_bug")
def open_modal(ack, shortcut, client, logger, body):
    # Acknowledge the shortcut request
    ack()

    try:
        # Call the views_open method using the built-in WebClient
        api_response = client.views_open(
            trigger_id=shortcut["trigger_id"],
            # A simple view payload for a modal
            view=
                {
                    "type": "modal",
                    "callback_id": "view-id",
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
                                            "text": "5️⃣ Huge (angry, pain, crying, $10^5 ARR)",
                                            "emoji": True
                                        },
                                        "value": "5"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "4️⃣ Large (anger, dismay, swearing, $10^4 ARR)",
                                            "emoji": True
                                        },
                                        "value": "4"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "3️⃣ Big (frustration, annoyance, $10^3 ARR)",
                                            "emoji": True
                                        },
                                        "value": "3"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "2️⃣ Medium (eye-rolling, $10^2 ARR)",
                                            "emoji": True
                                        },
                                        "value": "2"
                                    },
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "1️⃣ Small (may make you laugh instead of cry, $10^1 ARR)",
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
                            }
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
            )
        logger.info(api_response)
        
    except SlackApiError as e:
        logger.error("Error creating conversation: {}".format(e))

@app.view("view-id")
def view_submission(ack, client, body, view, logger):
    ack()

    user = body["user"]["id"]
    blocks = body["view"]["state"]["values"]

    bug_file = Bug()
    bug_file.site = get_value('site', 'site-action', blocks)
    bug_file.description = get_value('bug-description', 'bug-description-action', blocks)
    bug_file.vis = int(get_value('visibility','visibility-action', blocks))
    bug_file.impact = int(get_value('impact', 'impact-action', blocks))
    bug_file.to_reproduce = get_value('how-to-reproduce', 'how-to-reproduce-action', blocks)
    bug_file.expected = get_value('expected-behavior', 'expected-behavior-action', blocks)
    bug_file.config = get_value('config', 'config-action', blocks)

    # monday stuff
    api_key = os.environ.get("MONDAY_API_KEY")
    board_id = os.environ.get("BOARD_ID")

    apiUrl = "https://api.monday.com/v2"
    headers = {"Authorization" : api_key}

    # create item with bug file information
    print("bug_file.description", bug_file.description, type(bug_file.description))

    create_item = 'mutation ($myItemName: String!, $columnVals: JSON!) { create_item (board_id:'+board_id+', item_name:$myItemName, column_values:$columnVals) { id } }'
    vars = {
        'myItemName' : bug_file.description,
        'columnVals' : json.dumps({
            'status_11' : {'label' : bug_file.site},
            'numbers' : bug_file.vis,
            'numbers0' : bug_file.impact
        })
    }
    new_item = {'query' : create_item, 'variables' : vars}
    r = requests.post(url=apiUrl, json=new_item, headers=headers) # make request
    r_json = r.json()
    print(r_json)
    item_id = r_json["data"]["create_item"]["id"] # save item id

    # create update within newly created item
    body = "\""+"<p><strong>Description</strong></p>"+bug_file.description+"<p><strong>Visibility</strong></p>"+str(bug_file.vis)+"<p><strong>Impact</strong></p>"+str(bug_file.impact)+"<p><strong>To Reproduce</strong></p>"+bug_file.to_reproduce+"<p><strong>Expected behavior</strong></p>"+bug_file.expected+"<p><strong>Configuration</strong></p>"+bug_file.config+"\""
    print(body)

    create_update = 'mutation { create_update (item_id:'+item_id+', body:'+body+') { id } }'
    new_update = {'query' : create_update}
    r = requests.post(url=apiUrl, json=new_update, headers=headers) # make request
    print(r.json())

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))