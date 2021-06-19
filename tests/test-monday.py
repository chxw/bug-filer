from monday import add_file_to_column, add_file_to_update

update_id = "1054445315"
item_id = "1397158324"

# Upload file to monday.com
add_file_to_update(update_id=update_id)

# Upload file to files column
add_file_to_column(item_id)