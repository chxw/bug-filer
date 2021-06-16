import requests
import os
import json

apiUrl = "https://api.monday.com/v2"
api_key = os.environ.get("MONDAY_API_KEY")
headers = {"Authorization" : api_key}
board_id = os.environ.get("BOARD_ID")

def get_priority(imp, vis):
    if imp/vis >= 5/2:
        return "Critical"
    elif imp/vis >= 5/4:
        return "High"
    elif imp/vis >= 5/6:
        return "Medium"
    else:
        return "Low"

def create_item(site, description, visibility, impact):
    mutate_query = 'mutation ($myItemName: String!, $columnVals: JSON!) { create_item (board_id:'+board_id+', item_name:$myItemName, column_values:$columnVals) { id } }'
    vars = {
        'myItemName' : description,
        'columnVals' : json.dumps({
            'status_11' : {'label' : site},
            'numbers' : visibility,
            'numbers0' : impact,
            'status_18' : get_priority(impact, visibility)
        })
    }
    new_item = {'query' : mutate_query, 'variables' : vars}
    
    try:
        r = requests.post(url=apiUrl, json=new_item, headers=headers) # make request
        r_json = r.json()
        print(r_json)
        item_id = r_json["data"]["create_item"]["id"] # save item id
        return item_id

    except KeyError as e:
        print("Error creating monday item {0}".format(e))

def create_update(user, description, visibility_text, impact_text, to_reproduce, expected, config, item_id):
    headers = {"Authorization" : api_key}

    body = json.dumps("<p><strong>Describe the bug</strong></p>"+description+"<p></p><p><strong>Visibility</strong></p>"+visibility_text+"<p></p><p><strong>Impact</strong></p>"+impact_text+"<p></p><p><strong>To Reproduce</strong></p>"+to_reproduce+"<p></p><p><strong>Expected behavior</strong></p>"+expected+"<p></p><p><strong>Configuration (e.g. browser type, screen size, device)</strong></p>"+config+"<p></p><p><strong>Filed by</strong></p>"+user)

    mutate_query = 'mutation { create_update (item_id:'+item_id+', body:'+body+') { id } }'
    new_update = {'query' : mutate_query}
    try:
        r = requests.post(url=apiUrl, json=new_update, headers=headers) # make request
        r_json = r.json()
        print(r.json())
        update_id = r_json["data"]["create_update"]["id"] # save update id
        update_url = "https://www.databento.monday.com/boards/"+board_id+"/pulses/"+update_id
        return update_url

    except KeyError as e:
        print("Error creating monday update {0}".format(e))