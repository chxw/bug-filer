def get_value(block_id, action_id, blocks):
    try:
        value = blocks[block_id][action_id]['value']
    except KeyError:
        value = blocks[block_id][action_id]['selected_option']['value']
    if value == None:
        value = "N/A"
    return value

def get_text(block_id, action_id, blocks):
    try:
        return blocks[block_id][action_id]['selected_option']['text']['text']
    except KeyError:
        return "N/A"