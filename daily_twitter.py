import creds
from datetime import datetime
from utils.modules import (
    api_call,
    process_frostapi,
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
        'auth': (creds.client_id_frost, '')
        }

    rute_call_dict = {'url': creds.endpoint_rute}
    if read is False:
        data_frost = api_call('Frost API', **frost_call_dict).json()
    else:
        data_frost = read_file('data_frost.json')

    latest_observation = data_frost['data'][-1]['referenceTime']
    latest_observation = datetime.fromisoformat(latest_observation)

    if write is True:
        write_file('data_frost.json', data_frost)

    data_dict = process_frostapi(data_frost, 25)
    twitter_str = (
        "Gullingen siste 24t\n"
        f"{data_dict['first_timestamp']}\n"
        f"{data_dict['last_timestamp']}\n"
        f"Snø: {data_dict['snow']:.1f} cm\n"
        f"Regn: {data_dict['rain']:.1f} mm\n"
        f"Snitt.temp: {data_dict['avg_temp']:.1f} °C\n"
        f"Max temp: {data_dict['max_temp']:.1f} °C\n"
        f"Min temp: {data_dict['min_temp']:.1f} °C\n"
        f"Vind: {data_dict['avg_wind_speed']:.1f} m/s\n"
        f"Sterkeste vindkast: {data_dict['overall_max_wind_speed']:.1f} m/s"
        "\nEndring i snødybde: "
        f"{data_dict['snow_height_first']} cm\n"
        f"til {data_dict['snow_height_last']} cm"
        )
    twitter_post(creds.twitter_access_token, creds.twitter_access_token_secret,
                 creds.twitter_api_key, creds.twitter_api_key_secret,
                 twitter_str)


if __name__ == "__main__":
    main()
