import requests
import os
import json

apiUrl = "https://api.monday.com/v2"
api_key = os.environ.get("MONDAY_API_KEY")
board_id = os.environ.get("BOARD_ID")

def create_item(site, description, visibility, impact):
    headers = {"Authorization" : api_key}

    create_item = 'mutation ($myItemName: String!, $columnVals: JSON!) { create_item (board_id:'+board_id+', item_name:$myItemName, column_values:$columnVals) { id } }'
    vars = {
        'myItemName' : description,
        'columnVals' : json.dumps({
            'status_11' : {'label' : site},
            'numbers' : visibility,
            'numbers0' : impact
        })
    }
    new_item = {'query' : create_item, 'variables' : vars}
    r = requests.post(url=apiUrl, json=new_item, headers=headers) # make request
    r_json = r.json()
    print(r_json)
    item_id = r_json["data"]["create_item"]["id"] # save item id

    return item_id

def create_update(user, site, description, visibility, impact, to_reproduce, expected, config, item_id):
    headers = {"Authorization" : api_key}

    body = json.dumps("<p><strong>Describe the bug</strong></p>"+description+"<p></p><p><strong>Visibility</strong></p>"+str(visibility)+"<p></p><p><strong>Impact</strong></p>"+str(impact)+"<p></p><p><strong>To Reproduce</strong></p>"+to_reproduce+"<p></p><p><strong>Expected behavior</strong></p>"+expected+"<p></p><p><strong>Configuration (e.g. browser type, screen size, device)</strong></p>"+config+"<p></p><p><strong>Filed by</strong></p>"+user)

    create_update = 'mutation { create_update (item_id:'+item_id+', body:'+body+') { id } }'
    new_update = {'query' : create_update}
    r = requests.post(url=apiUrl, json=new_update, headers=headers) # make request
    r_json = r.json()
    print(r.json())
    update_id = r_json["data"]["create_update"]["id"] # save update id

    new_update = "https://www.databento.monday.com/boards/"+board_id+"/pulses/"+update_id

    return new_update