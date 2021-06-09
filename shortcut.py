import logging

logging.basicConfig(level=logging.DEBUG)

import os
from dotenv import load_dotenv
load_dotenv()

import requests
import json

from slack_bolt import App
from slack_bolt.authorization import AuthorizeResult
from slack_sdk import WebClient

# monday stuff
api_key = os.environ.get('MONDAY_API_KEY')
board_id = os.environ.get('BOARD_ID')

def authorize(enterprise_id, team_id, user_id, client: WebClient, logger):
    logger.info(f"{enterprise_id},{team_id},{user_id}")
    # You can implement your own logic here
    token = os.environ["SLACK_BOT_TOKEN"]
    return AuthorizeResult.from_auth_test_response(
        auth_test_response=client.auth_test(token=token),
        bot_token=token,
    )

app = App(signing_secret=os.environ["SLACK_SIGNING_SECRET"], authorize=authorize)

# Middleware
@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()

@app.event("message")
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

# Listens to incoming messages that contain "hello"
@app.message("hello")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click Me"},
                    "action_id": "button_click"
                }
            }
        ],
        text=f"Hey there <@{message['user']}>!"
    )

# The open_modal shortcut listens to a shortcut with the callback_id "open_modal"
@app.shortcut("file_bug")
def open_modal(ack, shortcut, client, logger, body):
    # Acknowledge the shortcut request
    ack()
    logger.info(body)
    # Call the views_open method using the built-in WebClient
    api_response = client.views_open(
        trigger_id=shortcut["trigger_id"],
        # A simple view payload for a modal
        view=
            {
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
                "type": "modal",
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
                        "element": {
                            "type": "multi_static_select",
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
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "platform",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                }
                            ],
                            "action_id": "static_select-action"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Site",
                            "emoji": True
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "Describe the bug",
                            "emoji": True
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True
                        }
                    },
                    {
                        "type": "input",
                        "element": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select an item",
                                "emoji": True
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "1️⃣ (login/signup, docs - getting started, access key management)",
                                        "emoji": True
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "2️⃣ clicks away",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "3️⃣ clicks away",
                                        "emoji": True
                                    },
                                    "value": "value-2"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "4️⃣ clicks away",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "5️⃣ clicks away",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                }
                            ],
                            "action_id": "static_select-action"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Visibility",
                            "emoji": True
                        }
                    },
                    {
                        "type": "input",
                        "element": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select an item",
                                "emoji": True
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "5️⃣ Huge (angry, pain, crying, $10^5 ARR)",
                                        "emoji": True
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "4️⃣ Large (anger, dismay, swearing, $10^4 ARR)",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "3️⃣ Big (frustration, annoyance, $10^3 ARR)",
                                        "emoji": True
                                    },
                                    "value": "value-2"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "2️⃣ Medium (eye-rolling, $10^2 ARR)",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "1️⃣ Small (may make you laugh instead of cry, $10^1 ARR)",
                                        "emoji": True
                                    },
                                    "value": "value-1"
                                }
                            ],
                            "action_id": "static_select-action"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Impact",
                            "emoji": True
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "To Reproduce",
                            "emoji": True
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "Expected behavior",
                            "emoji": True
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": True
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "Configuration (e.g. browser type, screen size, device)",
                            "emoji": True
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": False
                        },
                        "optional": True
                    }
                ]
            }
    )
    logger.debug(api_response)
    
# Start your app
if __name__ == "__main__":
    app.start(3000)