import creds
from datetime import datetime
from utils.modules import (
    api_call,
    process_frostapi,
    courier_message,
    read_file,
    write_file,
    local_to_utc,
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
        data_rute = api_call(**rute_call_dict).json()
        data_frost = api_call(**frost_call_dict).json()
    else:
        data_rute = read_file('data_rute.json')
        data_frost = read_file('data_frost.json')

    latest_observation = data_frost['data'][-1]['referenceTime']
    latest_observation = datetime.fromisoformat(latest_observation)
    print(latest_observation)

    latest_snow_removal = process_rute(data_rute)
    data_dict = process_frostapi(data_frost, 25)
    data_rute['latest_snow_removal'] = latest_snow_removal
    # Send notification message with courier
    list_id = 'testing'
    template = "BDERY25N6SMHJRM5TPWRN7BGHGFM"
    courier_message(creds.auth_token_courier, list_id, template, data_dict)


if __name__ == "__main__":
    main()
