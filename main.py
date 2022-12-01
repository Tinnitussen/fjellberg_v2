import json
import requests
from datetime import datetime, timedelta
import time
from trycourier import Courier
import creds

# Function for making API call
def api_call(url:str, parameters='', id='', secret=''):
    """API call for collecting JSON data"""

    # Making counter to limit tries
    count = 0

    while True:
        # Making get request
        try:
            api_data = requests.get(url, parameters, auth=(id, secret))
        
        except Exception as ex:
            print(ex)
            return False

        # Extract JSON data
        json = api_data.json()

        if api_data.status_code == 200:
            print(f'Data successfully retrieved from {url}!')
            break
        elif count>2:
            print(f'Failed connect {count} times.')
            print(f'API call for {url} unsuccessfull.')
            return False
        else:
            print(f'Failed connect {count} times.')
            print(f'Error! Returned status code {api_data.status_code}')
            message = json['error']['message']
            reason = json['error']['reason']
            print(f'Message: {message}')
            print(f'Reason: {reason}')
            time.sleep(20)
            count+=1
            continue
    return json

def write_file(filnavn:str, data):
    with open(filnavn,'w') as outfile:
       json.dump(data, outfile, indent=2)

def read_file(filnavn:str):
    with open(filnavn, 'r') as openfile:
        return json.load(openfile)

def main(write = False, local = False):
    """Run the program"""
    # Credentials
    # irute.no
    client_id_rute = creds.client_id_rute
    client_secret_rute = creds.client_secret_rute
    # frost API
    client_id_frost = creds.client_id_frost
    client_secret_frost = creds.client_secret_frost
    # Courier
    auth_token_courier = creds.auth_token_courier
    auth_token_courier_24 = creds.auth_token_courier_24
    # Daily email
    daily_summary = creds.daily_summary

    if local is True and write is True:
        print('"Local" cannot be true when "write" is true.')
        print('Can\'t write to file file when running locally.\nExiting...')
        quit()
    
    if local is False:
        if not daily_summary:
            # API call irute.no
            endpoint_rute = 'https://kart.irute.net/fjellbergsskardet_busses.json?_=1651561338966'
            data_rute = api_call(endpoint_rute, id=client_id_rute, secret=client_secret_rute)

        # API call frost API
        endpoint_frost = 'https://frost.met.no/observations/v0.jsonld'
        elements_frost = ('sum(precipitation_amount PT1H),'
        'air_temperature,'
        'surface_snow_thickness,'
        'wind_speed,'
        'max(wind_speed PT1H)')
        parameters_frost = {
            'sources': 'SN46220',
            'referencetime': 'latest',
            'elements': elements_frost,
            'timeresolutions': 'PT1H',
            'maxage': 'P1D',
            'limit': '24'
        }
        data_frost = api_call(endpoint_frost, parameters_frost, client_id_frost, client_secret_frost)

    if write is True:
        if not daily_summary:
            filnavn_rute = 'data_rute.json'
            write_file(filnavn_rute, data_rute)
        filnavn_frost = 'data_frost.json'
        write_file(filnavn_frost, data_frost)


    if local is True:
        filnavn_rute = 'data_rute.json'
        filnavn_frost = 'data_frost.json'
        data_frost = read_file(filnavn_frost)
        data_rute = read_file(filnavn_rute)
    
    if not daily_summary:
        # Data processing irute.no. Finding most recent snow removal.
        data_rute = data_rute['features']
        latest_snow_removal = None
        for element in data_rute:
            date = element['properties']['Date']
            date_object = datetime.strptime(date, '%H:%M:%S %d.%m.%Y')
            if latest_snow_removal is None:
                latest_snow_removal = date_object
            if date_object>latest_snow_removal:
                latest_snow_removal= date_object
        #Find the latest observations from frost API data.
        latest_observation = data_frost['data'][-1]['referenceTime'] # ISO format
        latest_observation = datetime.strptime(latest_observation, "%Y-%m-%dT%H:00:00.000Z")
    
        # irute.no is in CET while frost API is in UTC
        # Time is adjusted by +1

        # 1. Snow removal more recent than latest data from Frost API
        if latest_observation-latest_snow_removal<=timedelta(hours=0):
            num_iterations = 0
            print('Snow was removed very recently OR there is a problem with the data. \nExiting program...')
            quit()
        # 2. Snow removal >=24 hours
        elif latest_observation-latest_snow_removal>=timedelta(hours=23):
            num_iterations = 24
        # 3. Snow removal between 0 and 24 hours
        else:
            hours=int((str(latest_observation-latest_snow_removal))[:1])
            num_iterations = hours+1
    else:
        num_iterations = 24
    # Data processing
    snow = 0
    data_frost = data_frost['data']
    referenceTime_dict = {}
    data_dictionary = {}
    missing_data_dict = {}
    for i, data in enumerate(reversed(data_frost)):
        if i == num_iterations:
            break
        timestamp = data['referenceTime']
        timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:00:00.000Z")
        timestamp += timedelta(hours=1) # UTC to CET
        print(timestamp)
        referenceTime_dict[i] = timestamp
        data = data['observations']
        for observation in data:
            if observation['elementId'] not in data_dictionary.keys():
                data_dictionary[observation['elementId']] = [observation['value']]

            else:
                data_dictionary[observation['elementId']].append(observation['value'])

        # Samle en informasjon fra en måling
        try:
            temperature = data_dictionary['air_temperature'][-1]
            print(f'Lufttemperatur: {temperature} C')
        except KeyError:
            missing_data = 'air_temperature'
            print(f'{missing_data}: MISSING DATA')
            if timestamp not in missing_data_dict.keys():
                missing_data_dict[timestamp] = [missing_data]
            else:
                missing_data_dict[timestamp].append(missing_data)
        try:
            precipitation = data_dictionary["sum(precipitation_amount PT1H)"][-1]
            print(f'Nedbør: {precipitation} mm')
        except KeyError:
            missing_data = 'sum(precipitation_amount PT1H)'
            print(f'{missing_data}: MISSING DATA')
            if timestamp not in missing_data_dict.keys():
                missing_data_dict[timestamp] = [missing_data]
            else:
                missing_data_dict[timestamp].append(missing_data)
        try:
            snow_height = data_dictionary["surface_snow_thickness"][-1]
            print(f'Snøhøyde: {snow_height} cm')
        except KeyError:
            missing_data = 'surface_snow_thickness'
            print(f'{missing_data}: MISSING DATA')
            if timestamp not in missing_data_dict.keys():
                missing_data_dict[timestamp] = [missing_data]
            else:
                missing_data_dict[timestamp].append(missing_data)
        try:
            wind_speed = data_dictionary["wind_speed"][-1]
            print(f'Vindstyrke: {wind_speed} m/s')
        except KeyError:
            missing_data = 'wind_speed'
            print(f'{missing_data}: MISSING DATA')
            if timestamp not in missing_data_dict.keys():
                missing_data_dict[timestamp] = [missing_data]
            else:
                missing_data_dict[timestamp].append(missing_data)
        try:
            max_wind_speed = data_dictionary["max(wind_speed PT1H)"][-1]
            print(f'Sterkeste vindkast: {max_wind_speed} m/s\n')
        except KeyError:
            missing_data = 'max(wind_speed PT1H)'
            print(f'{missing_data}: MISSING DATA')
            if timestamp not in missing_data_dict.keys():
                missing_data_dict[timestamp] = [missing_data]
            else:
                missing_data_dict[timestamp].append(missing_data)

        # Converting to precipitation to snow under certain conditions
        if len(data_dictionary["surface_snow_thickness"])>1:
            delta_snow_1h = (data_dictionary["surface_snow_thickness"][-1]-
            data_dictionary["surface_snow_thickness"][-2])
        else:
            delta_snow_1h = 0
    
        if temperature<1 and delta_snow_1h>=0:
            snow += precipitation
    
    
    # Summary
    # Wind
    overall_max_wind_speed = max(data_dictionary["max(wind_speed PT1H)"])
    timestamp_omws = data_dictionary["max(wind_speed PT1H)"].index(overall_max_wind_speed)
    timestamp_omws = referenceTime_dict[timestamp_omws]
    avg_wind_speed = sum(data_dictionary['wind_speed'])/len(data_dictionary['wind_speed'])
    # Temp
    avg_temp = sum(data_dictionary["air_temperature"])/len(data_dictionary["air_temperature"])
    max_temp = max(data_dictionary["air_temperature"])
    min_temp = min(data_dictionary["air_temperature"])
    # Snow
    overall_snow_delta = (data_dictionary["surface_snow_thickness"][0]-
    data_dictionary["surface_snow_thickness"][-1])
    snow_height_first = data_dictionary["surface_snow_thickness"][0]
    snow_height_last = data_dictionary["surface_snow_thickness"][-1]
    # Rain
    sum_precipitation = sum(data_dictionary['sum(precipitation_amount PT1H)'])
    # Time
    first_timestamp = referenceTime_dict[max(referenceTime_dict.keys())]
    last_timestamp = referenceTime_dict[0]

    print('DATA SUMMARY')
    print('--------------------------')
    print(f'Nedbør som snø siste {num_iterations} timer: {snow} cm')
    print(f'Nedbør som regn siste {num_iterations} timer: {sum_precipitation} mm')
    print(f'Gjennomsnittlig temperatur siste {num_iterations} timer: {avg_temp:.2f} C')
    print(f'Høyeste temperatur: {max_temp} C')
    print(f'Laveste temperatur: {min_temp} C')
    print(f'Gjennomsnittlig vindstyrke siste {num_iterations} timer: {avg_wind_speed:.2f} m/s')
    print(f'Høyeste vindstyrke: {overall_max_wind_speed} m/s. Måling: {timestamp_omws}')
    print(f'Snøhøyde delta: {overall_snow_delta} cm. '
    f'Fra {snow_height_first} cm til {snow_height_last} cm')
    print(f'Siste måling: {last_timestamp}')
    print(f'Første måling: {first_timestamp}')

    # Missing data
    if missing_data_dict:
        for timestamp in missing_data_dict:
            print('-'*20)
            print(f'Missing data at {timestamp} UTC +1.\nElement(s) missing: {missing_data_dict[timestamp]}')
            print('This time is in UTC+1. Time in raw data is UTC.')
            print('(!)Conversion is done in the data processing(!)')

    # Conditions for notification
    notification = True
    if num_iterations<6 and snow-num_iterations>4:
        notification = True
    if daily_summary:
        notification = True
    if notification is True or snow>8:
        print('Notification information:')
        print(f'Snow: {snow}')
        print(f'Num iterations: {num_iterations}') 
        # Making dictionary for notification from data
        data_dict = {
        'num_iterations': f'{num_iterations}', 'snow': f'{snow:.2f}', 'sum_precipitation': f'{sum_precipitation:.2f}',
        'avg_temp': f'{avg_temp:.2f}', 'avg_wind_speed': f'{avg_wind_speed:.2f}', 
        'overall_max_wind_speed': f'{overall_max_wind_speed}', 'timestamp_omws': f'{timestamp_omws}',
        'last_timestamp': f'{last_timestamp}', 'first_timestamp': f'{first_timestamp}',
        'overall_snow_delta': f'{overall_snow_delta}', 'snow_height_first': f'{snow_height_first}',
        'snow_height_last': f'{snow_height_last}', 'max_temp': f'{max_temp}', 'min_temp': f'{min_temp}'
        }

        #Auth with courier
        if not daily_summary:
            client = Courier(auth_token=auth_token_courier)
            list_id = 'testing'
            mailing_list = [{'list_id': list_id}]
            template = "DVXWVCXH4DMAMAM0HRVTP1MVAGEZ"
            resp = client.send_message(
                message = {
                    'to': mailing_list,
                    'data': data_dict,
                    'template': template
                }
            )
            print(resp["requestId"])

        else:
            client = Courier(auth_token=auth_token_courier_24)
            list_id = 'testing'
            mailing_list = [{'list_id': list_id}]
            template = "BDERY25N6SMHJRM5TPWRN7BGHGFM"
            resp = client.send_message(
                message = {
                    'to': mailing_list,
                    'data': data_dict,
                    'template': template
                }
            )
            print(resp["requestId"])

    
    #"air_temperature"
    #"sum(precipitation_amount PT1H)"
    #"surface_snow_thickness"
    #"wind_speed"
    #"max(wind_speed PT1H)"
if __name__=="__main__":
    main(write=True, local=False)
