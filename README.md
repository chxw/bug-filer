# Slack Bug Filer

## Summary

File bugs as monday.com board items using Slack's UI. The Slack App registration id is: `A01DA26KJ81`.

For more information on how to use the app UI, see here: <https://databento.slab.com/posts/how-to-use-bug-filing-app-on-slack-8xap4rx1>.

### .env

This includes:

- Monday.com API key: Currently Chelsea's personal GraphQL Token. Can be found for any user in `/apps/manage/tokens` on monday.com
- Monday.com board_id: Currently Databento's #dev-bugs Monday board.
- Slack bot token: app token, with a granular permission model to request only the scopes necessary. These begin with `xoxb-`.
- Slack signing secret: Slack signs its requests using a secret that's unique to the app for security purposes. See <https://api.slack.com/authentication/verifying-requests-from-slack>.
- Slack app token: Special tokens used with specific APIs that are related to the app across all organizations it's installed in.
- Slack test channel id: Corresponds to private #test channel, used by Chelsea to work out app kinks.
- Slack channel id: Corresponds to Databento's #dev-bugs Slack channel.

### Data folder

This includes:

- `history.csv`: History of all transactions made by this app.
- `output.txt`: All helper print() lines used when writing this app were updated to write to output.txt.

### Helpers

This includes:

- `bug-file.json`: Previously used to upload JSON-formatted Slack blocks to the main.py file. This is no longer used, and the JSON is included in the main.py because values in the JSON need to be parametrized.
- `bug.py`: Contains definition of Bug class.
- `monday.py`: Contains helper functions related to querying and mutating Monday.com board using Monday's API.
- `util.py`: Contains misc. helper functions.

### Main.py

This file contains functions that deal with the following user interactions. For more information on what is meant by the corresponding user interactions, please refer to this document: <https://databento.slab.com/posts/how-to-use-bug-filing-app-on-slack-8xap4rx1>.

#### Global shortcut

```python
@app.shortcut("file_bug")
def file_bug(ack, shortcut, body, client):
```

#### Message Shortcut

```python
@app.action("create_item")
def file_bug_with_image(ack, client, body):
```

#### Share file

```python
@app.event(
    event={"type": "message", "subtype": "file_share"}
)
def handle_file_share(ack, client, body):
```

## Files

```bash
.
├── README.md
├── data
│   ├── history.csv
│   └── output.txt
├── helpers
│   ├── __init__.py
│   ├── bug-file.json
│   ├── bug.py
│   ├── monday.py
│   └── util.py
├── main.py
├── requirements.txt
└── tests
    ├── test-df.py
    └── test-monday.py
```

## Instructions

1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip3 install -r requirements.txt`
4. `source .env`
5. `python3 main.py`

## References

- <https://api.slack.com/>
- <https://monday.com/developers/v2>
- <https://community.monday.com/t/upload-file-using-python-and-getting-unsupported-query-error/21427/8>
