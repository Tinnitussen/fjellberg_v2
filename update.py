from trycourier import Courier
import requests
import json
import creds

# Courier auth
client = Courier(auth_token=creds.auth_token_courier)
list_id = 'fjellberg_daily'

# Get IDs for current subscribers to the mailing list
subscriptions_resp = client.lists.get_subscriptions(list_id)
subscribers_ids = [user['recipientId'] for user in subscriptions_resp['items']]
print(f'Current subscribers to {list_id}: {subscribers_ids}')

# Get CSV from sheet and convert to text
mailing_list = requests.get(
    f'https://docs.google.com/spreadsheet/ccc?key={creds.sheet_id}&output=csv'
    )
mailing_list = mailing_list.text
# Seperate based on line so each user has its' own list of information
mailing_list = mailing_list.split('\r\n')
# Delete top line of spreadsheet
del mailing_list[0]
# Convert it into courier format
for recipient in mailing_list:
    recipient_info = recipient.split(',')
    recipient_id = recipient_info[0]
    recipient_mail = {"email": recipient_info[1]}
    recipient_added_timestamp = recipient_info[2]
    if recipient_id not in subscribers_ids:
        # Add to courier userbase
        add_user_resp = client.profiles.add(recipient_id, recipient_mail)
        print(f'Adding {recipient_mail} to the userbase and mailing list.')
        print(add_user_resp)
        # Subscribe user that was added to the mailing list
        subscribe_user_resp = client.lists.subscribe(list_id, recipient_id)

# Get the list information
resp = client.lists.get_subscriptions(list_id)
print(json.dumps(resp, indent=2))
