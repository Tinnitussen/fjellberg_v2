import creds
from datetime import datetime, timedelta
from utils.modules import (
    api_call,
    process_frostapi,
    courier_message,
    read_file,
    write_file,
    process_rute
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
        data_rute = api_call('Rute', **rute_call_dict).json()
    else:
        data_frost = read_file('data_frost.json')
        data_rute = read_file('data_rute.json')

    if write is True:
        write_file('data_frost.json', data_frost)
        write_file('data_rute', data_rute)

    latest_snow_removal = process_rute(data_rute)
    data_dict = process_frostapi(data_frost, latest_snow_removal, 25)

    latest_observation = data_frost['data'][-1]['referenceTime']
    latest_observation = datetime.fromisoformat(latest_observation)

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
        snow_since_removed = snow_check_dict['snow']
        data_dict['snow_since_removed'] = (
            f'Snø siden sist brøytet {snow_since_removed} cm'
        )

    # Send notification message with courier
    list_id = 'testing'
    template = "BDERY25N6SMHJRM5TPWRN7BGHGFM"
    courier_message(creds.auth_token_courier, list_id, template, data_dict)


if __name__ == "__main__":
    main()
