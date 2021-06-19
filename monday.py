import requests
import os
import json

apiUrl = "https://api.monday.com/v2"
api_key = os.environ.get("MONDAY_API_KEY")
headers = {"Authorization" : api_key}
board_id = os.environ.get("BOARD_ID")

def _get_priority(imp, vis):
    '''
    Input: Impact (int), Visibility (int)

    Calculate the Priority value (critical, high, medium, low) from the Impact / Visbility matrix. 

    Returns: Priority (string)
    '''
    if imp/vis >= 5/2:
        return "Critical"
    elif imp/vis >= 5/4:
        return "High"
    elif imp/vis >= 5/6:
        return "Medium"
    else:
        return "Low"

def create_item(bug):
    '''
    Input: bug object

    Create monday item on board_id (find in .env).
    '''
    mutate_query = 'mutation ($myItemName: String!, $columnVals: JSON!) { create_item (board_id:'+board_id+', item_name:$myItemName, column_values:$columnVals) { id } }'
    vars = {
        'myItemName' : bug.description,
        'columnVals' : json.dumps({
            'status_11' : {'label' : bug.site},
            'numbers' : bug.visibility,
            'numbers0' : bug.impact,
            'status_18' : _get_priority(bug.impact, bug.visibility)
        })
    }
    new_item = {'query' : mutate_query, 'variables' : vars}
    
    try:
        r = requests.post(url=apiUrl, json=new_item, headers=headers) # make request
        r_json = r.json()
        # print(r_json)
        bug.monday_item_id = r_json["data"]["create_item"]["id"] # save item id

    except (IndexError, KeyError, TypeError) as e:
        print("Error creating monday item {0}".format(e))

def create_update(bug):
    '''
    Input: bug object

    Create monday update in a monday item, retreivied from the bug object's attribute bug.monday_item_id.
    '''
    # Format Monday update
    body = json.dumps(
        "<p><strong>Describe the bug</strong></p>"+bug.description+
        "<p></p><p><strong>Visibility</strong></p>"+bug.visibility_text+
        "<p></p><p><strong>Impact</strong></p>"+bug.impact_text+
        "<p></p><p><strong>To Reproduce</strong></p>"+bug.to_reproduce+
        "<p></p><p><strong>Expected behavior</strong></p>"+bug.expected+
        "<p></p><p><strong>Configuration (e.g. browser type, screen size, device)</strong></p>"+bug.config+
        "<p></p><p><strong>Filed by</strong></p>"+bug.name
        )

    mutate_query = 'mutation { create_update (item_id:'+bug.monday_item_id+', body:'+body+') { id } }'
    new_update = {'query' : mutate_query}
    try:
        r = requests.post(url=apiUrl, json=new_update, headers=headers) # make request
        r_json = r.json()
        # print(r.json())
        bug.monday_update_id = r_json["data"]["create_update"]["id"] # save update id
        bug.monday_item_url = "https://databento.monday.com/boards/"+board_id+"/pulses/"+bug.monday_item_id # save update url
        bug.monday_update_url = bug.monday_item_url+"/posts/"+bug.monday_update_id

    except (IndexError, KeyError, TypeError) as e:
        print("Error creating monday update {0}".format(e))

def add_file_to_update(update_id, file):
    '''
    Input: update_id

    Add file to monday update (update_id) using monday.com's /v2/file endpoint.
    '''
    apiUrl = "https://api.monday.com/v2/file"
    q = f"""
            mutation add_file($file: File!) {{
                add_file_to_update (update_id: {int(update_id)},
                            file: $file
                        ){{
                    id
                }}
            }}
        """

    files = {
        'query': (None, q, 'image/png'),
        'variables[file]': (file, open(file, 'rb'), 'multipart/form-data', {'Expires': '0'})
    }

    try:
        r = requests.post(url=apiUrl, files=files, headers=headers) #
        r_json = r.json()
        print(r_json)

    except (IndexError, KeyError, TypeError) as e:
        print("Error uploading file to monday update {0}".format(e))
    
def add_file_to_column(item_id, file):
    '''
    Input: item_id

    Add file to monday update (item_id) using monday.com's /v2/file endpoint.
    '''
    apiUrl = "https://api.monday.com/v2/file"
    q = f"""
            mutation add_file($file: File!) {{
                add_file_to_column (item_id: {int(item_id)},
                            column_id: files,
                            file: $file
                        ){{
                    id
                }}
            }}
        """

    files = {
        'query': (None, q, 'image/png'),
        'variables[file]': (file, open(file, 'rb'), 'multipart/form-data', {'Expires': '0'})
    }
    try: 
        r = requests.post(url=apiUrl, files=files, headers=headers)
        r_json = r.json()
        print(r_json)
    except (IndexError, KeyError, TypeError) as e:
        print("Error adding file to column on monday {0}".format(e))
