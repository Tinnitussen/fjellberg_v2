import os
if os.path.exists('creds_local.py'):
    import creds_local_testing
    creds_local_testing.set_environment()
# irute.no
client_id_rute = os.environ.get('CLIENT_ID_RUTE')
client_secret_rute = os.environ.get('CLIENT_SECRET_RUTE')
endpoint_rute = os.environ.get('ENDPOINT_RUTE')
# frost API
client_id_frost = os.environ.get('CLIENT_ID_FROST')
client_secret_frost = os.environ.get('CLIENT_SECRET_FROST')
# Checking to see if daily summary should be run
daily_summary = os.environ.get('DAILY_SUMMARY')
# Courier
auth_token_courier = os.environ.get('AUTH_TOKEN_COURIER')
auth_token_courier_24 = os.environ.get('AUTH_TOKEN_COURIER_24')
# Spreadsheet ID
sheet_id = os.environ.get('SHEET_ID')
# Twitter
twitter_api_key = os.environ.get('TWITTER_API_KEY')
twitter_api_key_secret = os.environ.get('TWITTER_API_KEY_SECRET')
twitter_bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
twitter_notification = os.environ.get('TWITTER_NOTIFICATION')
