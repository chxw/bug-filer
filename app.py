import logging

import os
from dotenv import load_dotenv

import requests
import json

from slack_sdk import WebClient
from slack_sdk.web import SlackResponse

from slack_bolt import App, Ack
from slack_bolt.workflows.step import Configure, Update, Complete, Fail, Wor

logging.basicConfig(level=logging.DEBUG)

# Load .env file
load_dotenv()

# monday stuff
api_key = os.environ.get('MONDAY_API_KEY')
board_id = os.environ.get('BOARD_ID')

# slack stuff
# Initializes your app with your bot token and signing secret
app = App()

@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()

# https://api.slack.com/tutorials/workflow-builder-steps

def edit(ack: Ack, step, configure: Configure):
    ack()
    configure(
        blocks=[
            {
                "title": {
                    "type": "plain_text",
                    "text": "File a bug",
                    "emoji": true
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit",
                    "emoji": true
                },
                "type": "modal",
                "close": {
                    "type": "plain_text",
                    "text": "Cancel",
                    "emoji": true
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "This form will submit your bug to the #dev-bugs board on monday.com",
                            "emoji": true
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
                                "emoji": true
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "multidocs",
                                        "emoji": true
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "platform",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                }
                            ],
                            "action_id": "static_select-action"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Site",
                            "emoji": true
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "Describe the bug",
                            "emoji": true
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": true
                        }
                    },
                    {
                        "type": "input",
                        "element": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select an item",
                                "emoji": true
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "1️⃣ (login/signup, docs - getting started, access key management)",
                                        "emoji": true
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "2️⃣ clicks away",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "3️⃣ clicks away",
                                        "emoji": true
                                    },
                                    "value": "value-2"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "4️⃣ clicks away",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "5️⃣ clicks away",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                }
                            ],
                            "action_id": "static_select-action"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Visibility",
                            "emoji": true
                        }
                    },
                    {
                        "type": "input",
                        "element": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select an item",
                                "emoji": true
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "5️⃣ Huge (angry, pain, crying, $10^5 ARR)",
                                        "emoji": true
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "4️⃣ Large (anger, dismay, swearing, $10^4 ARR)",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "3️⃣ Big (frustration, annoyance, $10^3 ARR)",
                                        "emoji": true
                                    },
                                    "value": "value-2"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "2️⃣ Medium (eye-rolling, $10^2 ARR)",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "1️⃣ Small (may make you laugh instead of cry, $10^1 ARR)",
                                        "emoji": true
                                    },
                                    "value": "value-1"
                                }
                            ],
                            "action_id": "static_select-action"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Impact",
                            "emoji": true
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "To Reproduce",
                            "emoji": true
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": true
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "Expected behavior",
                            "emoji": true
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": true
                        }
                    },
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "Configuration (e.g. browser type, screen size, device)",
                            "emoji": true
                        },
                        "element": {
                            "type": "plain_text_input",
                            "multiline": false
                        },
                        "optional": true
                    }
                ]
            }
        ]
    )

def save(ack: Ack, view: dict, update: Update):
    pass

def execute(step: dict, client: WebClient, complete: Complete, fail: Fail):
    pass

# Create a new WorkflowStep instance
ws = WorkflowStep(
    callback_id="new_monday_item",
    edit=edit,
    save=save,
    execute=execute,
)
# Pass Step to set up listeners
app.step(ws)
    
# Start your app
if __name__ == "__main__":
    app.start(3000)
    