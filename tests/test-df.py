import pandas as pd

update_id = 1054445315
# get item_id
df = pd.read_csv('history.csv', sep=',',header=0, error_bad_lines=False)
df.set_index('monday_update_id', inplace=True)
item_id = str(df['monday_item_id'][update_id])