import requests
import time
import json
from datetime import datetime
import pytz
from trycourier import Courier
import tweepy


def api_call(name='Not specified', **kwargs) -> requests.Response:
    """Make HTTP requests with requests library"""
    connection_tries = 0
    while True:
        try:
            r = requests.get(**kwargs)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            print('Connection timed out. Retrying...')
            time.sleep(15)
            if connection_tries == 3:
                print('Connection failed 3 times. Exiting...')
                raise SystemExit(100)
            connection_tries += 1
            continue
        except Exception as err:
            raise SystemExit(err)
        print(f'Data successfully retrieved from {name}')
        return r


def write_file(filnavn: str, data: json):
    with open(filnavn, 'w') as outfile:
        json.dump(data, outfile, indent=2)


def read_file(filnavn: str):
    with open(filnavn, 'r') as openfile:
        return json.load(openfile)


def local_to_utc(date):
    """Convert from local time in Oslo to UTC timeformat"""
    date_object = datetime.strptime(date, '%H:%M:%S %d.%m.%Y')
    local_timezone = pytz.timezone('Europe/Oslo')
    local_dt = local_timezone.localize(date_object, is_dst=True)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def utc_to_local(datetime_utc):
    """Convert from UTC to Oslo local time timeformat as userfriendly str"""
    local_timezone = pytz.timezone('Europe/Oslo')
    local = datetime_utc.astimezone(local_timezone)
    local_str = local.strftime("%d.%m.%Y %H:%M")

    return local_str


def process_rute(data_rute) -> dict:
    data_rute = data_rute['features']
    latest_snow_removal = None
    for element in data_rute:
        date = element['properties']['Date']
        date_dt = local_to_utc(date)
        name = element['properties']['NAME']
        status = element['properties']['STATUS']
        if status == 'online':
            print('Snow removal is in progress.')
            print('Exiting...')
            raise SystemExit(0)
        print(f'{name} last active {date_dt}. Current status {status}')
        if latest_snow_removal is None:
            latest_snow_removal = date_dt
        if date_dt > latest_snow_removal:
            latest_snow_removal = date_dt

    print(f'Last snow removal was at {latest_snow_removal}')
    return latest_snow_removal


def process_frostapi(data_frost, latest_snow_removal, num_iterations) -> dict:
    """Process data from Frost API"""
    snow = 0
    rain = 0
    data_frost = data_frost['data']
    referenceTime_dict = {}
    data_dictionary = {}
    missing_data_dict = {}
    missing_data = False
    element_list = [
        "air_temperature",
        "sum(precipitation_amount PT1H)",
        "surface_snow_thickness",
        "wind_speed",
        "max(wind_speed PT1H)"
        ]

    # Initialize the dictionary with keys and empty lists as values
    for element in element_list:
        data_dictionary[element] = []
        missing_data_dict[element] = []

    # Process data from frost API
    for i, data in enumerate(reversed(data_frost)):
        if i == num_iterations:
            break
        timestamp = data['referenceTime']
        timestamp = datetime.fromisoformat(timestamp)
        print(timestamp)
        referenceTime_dict[i] = timestamp
        data = data['observations']

        observation_list = []
        for observation in data:
            data_dictionary[observation['elementId']].append(
                observation['value'])
            observation_list.append(observation['elementId'])

        # Missing data
        skip = False
        for element in element_list:
            if element not in observation_list:
                missing_data = True
                missing_data_dict[element].append(timestamp)
                print(f'{element} MISSING!')
                skip = True
        if skip is True:
            print('(!!!)skip(!!!)\n')
            continue

        # Samle en informasjon fra en måling
        temperature = data_dictionary['air_temperature'][-1]
        print(f'Lufttemperatur: {temperature} C')
        precipitation = data_dictionary["sum(precipitation_amount PT1H)"][-1]
        print(f'Nedbør: {precipitation} mm')
        snow_height = data_dictionary["surface_snow_thickness"][-1]
        print(f'Snøhøyde: {snow_height} cm')
        if len(data_dictionary["wind_speed"]) > 0:
            wind_speed = data_dictionary["wind_speed"][-1]
            print(f'Vindstyrke: {wind_speed} m/s')
        if len(data_dictionary["max(wind_speed PT1H)"]) > 0:
            max_wind_speed = data_dictionary["max(wind_speed PT1H)"][-1]
            print(f'Sterkeste vindkast: {max_wind_speed} m/s\n')
        else:
            print()
        if temperature < 1:
            snow += precipitation
        else:
            rain += precipitation

    # Summary
    # Wind
    overall_max_wind_speed = max(data_dictionary["max(wind_speed PT1H)"])
    timestamp_omws = (
        data_dictionary["max(wind_speed PT1H)"]
        .index(overall_max_wind_speed)
        )
    timestamp_omws = referenceTime_dict[timestamp_omws]
    avg_wind_speed = (
        sum(data_dictionary['wind_speed']) /
        len(data_dictionary['wind_speed'])
        )
    # Temp
    avg_temp = (
        sum(data_dictionary["air_temperature"]) /
        len(data_dictionary["air_temperature"])
        )
    max_temp = max(data_dictionary["air_temperature"])
    min_temp = min(data_dictionary["air_temperature"])
    # Snow
    overall_snow_delta = (
        data_dictionary["surface_snow_thickness"][0] -
        data_dictionary["surface_snow_thickness"][-1]
        )
    snow_height_last = data_dictionary["surface_snow_thickness"][0]
    snow_height_first = data_dictionary["surface_snow_thickness"][-1]
    # Time
    first_timestamp = referenceTime_dict[max(referenceTime_dict.keys())]
    last_timestamp = referenceTime_dict[0]

    print('DATA SUMMARY')
    print('--------------------------')
    print(f'Nedbør som snø siste {num_iterations-1} timer: {snow:.1f} cm')
    print(f'Nedbør som regn siste {num_iterations-1} timer: {rain} mm')
    print(
        f'Gjennomsnittlig temperatur siste '
        f'{num_iterations-1} timer: {avg_temp:.2f} C'
        )
    print(f'Høyeste temperatur: {max_temp} C')
    print(f'Laveste temperatur: {min_temp} C')
    print(
        f'Gjennomsnittlig vindstyrke siste {num_iterations-1} timer: '
        f'{avg_wind_speed:.2f} m/s'
        )
    print(
        f'Høyeste vindstyrke: {overall_max_wind_speed} m/s. '
        f'Måling: {timestamp_omws}'
        )
    print(
        f'Snøhøyde delta: {overall_snow_delta:.1f} cm. '
        f'Fra {snow_height_first} cm til {snow_height_last} cm'
        )
    print(f'Siste måling: {last_timestamp}')
    print(f'Første måling: {first_timestamp}')

    # Missing data
    if missing_data is True:
        for element in missing_data_dict:
            if len(missing_data_dict[element]) > 0:
                for index in range(len(missing_data_dict[element])):
                    print('-'*20)
                    print(
                        f'Missing data at {missing_data_dict[element][index]}'
                        f'UTC +1.\nElement(s) missing: {element}'
                        )

    hours = num_iterations-1
    # Making data local time for the email notification
    timestamps = [
        last_timestamp,
        timestamp_omws,
        first_timestamp,
        latest_snow_removal
        ]
    timestamps_cet = [utc_to_local(timestamp) for timestamp in timestamps]
    last_timestamp_cet = timestamps_cet[0]
    timestamp_omws_cet = timestamps_cet[1]
    first_timestamp_cet = timestamps_cet[2]
    latest_snow_removal_cet = timestamps_cet[3]

    data_dict = {
            'num_iterations': f'{hours}',
            'snow': f'{snow:.1f}',
            'rain': f'{rain:.1f}',
            'avg_temp': f'{avg_temp:.2f}',
            'avg_wind_speed': f'{avg_wind_speed:.2f}',
            'overall_max_wind_speed': f'{overall_max_wind_speed:.1f}',
            'timestamp_omws': f'{timestamp_omws_cet}',
            'last_timestamp': f'{last_timestamp_cet}',
            'first_timestamp': f'{first_timestamp_cet}',
            'overall_snow_delta': f'{overall_snow_delta:.1f}',
            'snow_height_first': f'{snow_height_first}',
            'snow_height_last': f'{snow_height_last}',
            'max_temp': f'{max_temp:.1f}',
            'min_temp': f'{min_temp:.1f}',
            'latest_snow_removal': f'{latest_snow_removal_cet}'
        }
    return data_dict


def courier_message(auth_token, list_id, template, data_dict):
    client = Courier(auth_token=auth_token)
    message = {
            'to': [{'list_id': list_id}],
            'data': data_dict,
            'template': template
        }
    resp = client.send_message(message=message)
    print(resp["requestId"])


def twitter_post(access_token, access_token_secret,
                 api_key, api_key_secret, post_str):
    api = tweepy.Client(
        None, api_key, api_key_secret,
        access_token, access_token_secret
        )
    api.create_tweet(text=post_str)
