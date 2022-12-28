from datetime import datetime, timedelta
import pytz
import creds
import requests
from utils.modules import (
    api_call,
    process_frostapi,
    process_rute,
    courier_message,
    write_file,
    read_file
)


def main(write=False, read=False):
    # Checking to see if notification was sent <= 3 hours ago
    endpoint_read = (
        'https://api.thingspeak.com/channels/1994784/'
        f'feeds.json?api_key={creds.things_read_key}&results=2'
    )
    try:
        notification_iso = requests.get(endpoint_read)
        notification_iso = notification_iso.json()['feeds'][-1]['field1']
        notification_iso = notification_iso.replace(' ', '+')
        notif_timediff = None
        last_notification = datetime.fromisoformat(notification_iso)
        current_time = datetime.now(pytz.utc)
        notif_timediff = current_time - last_notification
    except Exception as err:
        print(err)

    if notif_timediff:
        if notif_timediff <= timedelta(hours=3):
            print('It is less than 3 hours since last notification was sent.')
            print('Exiting...')
            raise SystemExit(0)

    endpoint_frost = 'https://frost.met.no/observations/v0.jsonld'
    elements_frost = (
        'sum(precipitation_amount PT1H),'
        'air_temperature, surface_snow_thickness, wind_speed,'
        'max(wind_speed PT1H)'
        )

    parameters_frost = {
        'sources': 'SN46220',
        'referencetime': 'latest',
        'elements': elements_frost,
        'timeresolutions': 'PT1H',
        'maxage': 'P1D',
        'limit': '24'
    }

    frost_call_dict = {
        'url': endpoint_frost, 'params': parameters_frost,
        'auth': (creds.client_id_frost, '')
        }

    rute_call_dict = {'url': creds.endpoint_rute}

    if read is False:
        data_frost = api_call('Frost API', **frost_call_dict).json()
        data_rute = api_call('Rute', **rute_call_dict).json()
    else:
        data_frost = read_file('data_frost.json')
        data_rute = read_file('data_rute.json')

    if write is True:
        write_file('data_frost.json', data_frost)
        write_file('data_rute.json', data_rute)

    latest_snow_removal = process_rute(data_rute)

    latest_observation = data_frost['data'][-1]['referenceTime']
    latest_observation = datetime.fromisoformat(latest_observation)

    if latest_observation-latest_snow_removal <= timedelta(hours=0):
        num_iterations = 0
        print(
            'Snow was removed very recently OR'
            'there is a problem with the data.'
            '\nExiting program...'
            )
        raise SystemExit(0)

    # 2. Snow removal >=24 hours
    elif latest_observation-latest_snow_removal >= timedelta(hours=24):
        num_iterations = 25
    # 3. Snow removal between 0 and 24 hours
    else:
        timedifferential = latest_observation-latest_snow_removal
        # Get timedelta in seconds
        total_seconds = timedifferential.total_seconds()
        print(total_seconds)
        # Turn in to hours and round down for conservative approach
        hours = int(total_seconds/3600)
        print(hours)
        num_iterations = hours+1

    data_dict = process_frostapi(
        data_frost, latest_snow_removal, num_iterations
        )
    snow = float(data_dict['snow'])
    # Conditions for notification
    notification = False
    if num_iterations < 6 and snow-num_iterations > 4:
        notification = True

    if notification is True or snow > 8:
        # Writing notification time file
        iso_string = datetime.now(pytz.utc).isoformat()
        post_date = (
            'https://api.thingspeak.com/update?'
            f'api_key={creds.things_write_key}&field1='+iso_string
        )
        try:
            requests.get(post_date)
        except Exception as err:
            print("Couldn't post timestamp to thingspeak.")
            print(err)

        print('Notification information:')
        print(f'Snow: {snow}')
        print(f'Num iterations: {num_iterations}')
        # Send notification message with courier
        list_id = 'fjellberg_daily'
        template = "DVXWVCXH4DMAMAM0HRVTP1MVAGEZ"
        courier_message(creds.auth_token_courier, list_id, template, data_dict)


if __name__ == "__main__":
    main()
