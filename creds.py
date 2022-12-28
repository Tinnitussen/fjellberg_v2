import os
if os.path.exists('creds_local.py'):
    import creds_local
    creds_local.set_environment()
# irute.no
endpoint_rute = os.environ.get('ENDPOINT_RUTE')
# frost API
client_id_frost = os.environ.get('CLIENT_ID_FROST')
# Courier
auth_token_courier = os.environ.get('AUTH_TOKEN_COURIER')
# Spreadsheet ID
sheet_id = os.environ.get('SHEET_ID')
# Twitter
twitter_api_key = os.environ.get('TWITTER_API_KEY')
twitter_api_key_secret = os.environ.get('TWITTER_API_KEY_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
# Thingspeak
things_read_key = os.environ.get('THINGS_READ_KEY')
things_write_key = os.environ.get('THINGS_WRITE_KEY')
