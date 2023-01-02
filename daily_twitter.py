import creds
from datetime import datetime, timedelta
import os
from utils.modules import (
    api_call,
    process_frostapi,
    process_rute,
    twitter_post,
    write_file,
    read_file
)


def main(write=False, read=False):
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
        'auth': (creds.client_id_frost, creds.client_secret_frost)
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
        write_file('data_rute', data_rute)

    latest_snow_removal = process_rute(data_rute)
    NUM_ITERATIONS = int(os.environ.get('NUM_ITERATIONS'))
    data_dict = process_frostapi(
        data_frost,
        latest_snow_removal,
        NUM_ITERATIONS
        )

    latest_observation = data_frost['data'][-1]['referenceTime']
    latest_observation = datetime.fromisoformat(latest_observation)

    twitter_str = (
        "Gullingen siste 12t\n"
        f"{data_dict['first_timestamp']}\n"
        f"{data_dict['last_timestamp']}\n"
        f"Snø {data_dict['snow']} cm\n"
        f"Regn {data_dict['rain']} mm\n"
        f"Snitt.temp {data_dict['avg_temp']} °C\n"
        f"Max {data_dict['max_temp']} °C\n"
        f"Min {data_dict['min_temp']} °C\n"
        f"Vind {data_dict['avg_wind_speed']} m/s\n"
        f"Max vind {data_dict['overall_max_wind_speed']} m/s"
        "\nEndring snødybde "
        f"{data_dict['snow_height_first']} "
        f"til {data_dict['snow_height_last']} cm\n"
        f"Sist brøytet {data_dict['latest_snow_removal']}"
        )

    timedifferential = latest_observation-latest_snow_removal
    if (timedifferential >= timedelta(hours=0) and
       timedifferential <= timedelta(hours=24)):
        total_seconds = timedifferential.total_seconds()
        hours = int(total_seconds/3600)
        print(hours)
        num_iterations = hours+1
        snow_check_dict = process_frostapi(
            data_frost, latest_snow_removal, num_iterations
            )
        twitter_str += (
            "\nSnø fra sist brøytet "
            f"{snow_check_dict['snow']} cm"
            )

    twitter_post(creds.twitter_access_token, creds.twitter_access_token_secret,
                 creds.twitter_api_key, creds.twitter_api_key_secret,
                 twitter_str)


if __name__ == "__main__":
    main()
