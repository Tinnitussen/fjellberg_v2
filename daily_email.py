import creds
from datetime import datetime
from utils.modules import (
    api_call,
    process_frostapi,
    courier_message
)


def main():

    # Frost API
    # ------------------------------------------------------------
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

    data_frost = api_call(**frost_call_dict).json()
    latest_observation = data_frost['data'][-1]['referenceTime']
    latest_observation = datetime.fromisoformat(latest_observation)
    print(latest_observation)

    data_dict = process_frostapi(data_frost, 24)
    # Send notification message with courier
    list_id = 'testing'
    template = "BDERY25N6SMHJRM5TPWRN7BGHGFM"
    courier_message(creds.auth_token_courier, list_id, template, data_dict)
