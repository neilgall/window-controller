
import boto3
import json
import time
import logging
from alexa.skills.smarthome import AlexaResponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

aws_iot = boto3.client('iot-data')


_DEVICES = [
    {
        'friendly_name': 'Fresh Air',
        'description': 'Windows in Family Room',
        'endpoint_id': 'fresh-air'
    },
    {
        'friendly_name': 'Garden Fairy Lights',
        'description': 'Fairy Lights all around the Garden',
        'endpoint_id': 'garden-lights'    
    }
]


def error(**kwargs):
    """
    Build an error response
    """
    rsp = AlexaResponse(name='ErrorResponse', payload=kwargs).get()
    logger.debug(f'lambda handler failed; response: {json.dumps(rsp)}')
    return rsp


def success(obj):
    """
    Log a successful response object
    """
    logger.debug(f'lambda handler success; response: {json.dumps(obj)}')
    return obj


def discover_devices(request):
    """
    Discover the declared devices this handler supports
    """
    command = request['directive']['header']['name']
    if command == 'Discover':
        adr = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')
        capability_alexa = adr.create_payload_endpoint_capability()
        capability_alexa_powercontroller = adr.create_payload_endpoint_capability(
            interface='Alexa.PowerController',
            supported=[{'name': 'powerState'}])
        for device in _DEVICES:               
            adr.add_payload_endpoint(
                capabilities=[capability_alexa, capability_alexa_powercontroller],
                **device
            )
        return success(adr.get())


def control_device(request):
    """
    Control a specific device
    """
    power_state_value = 'OFF' if request['directive']['header']['name'] == 'TurnOff' else 'ON'
    endpoint_id = request['directive']['endpoint']['endpointId']
    correlation_token = request['directive']['header']['correlationToken']

    # Check for an error when setting the state
    state_set = set_device_state(endpoint_id=endpoint_id, value=power_state_value)
    if state_set is None:
        return error(type='ENDPOINT_UNREACHABLE', message='Unable to reach endpoint database.')
    elif not state_set:
        return error(type='ENDPOINT_UNREACHABLE', message='I did not get a response from the device controller.')

    apcr = AlexaResponse(correlation_token=correlation_token)
    apcr.add_context_property(namespace='Alexa.PowerController', name='powerState', value=power_state_value)
    return success(apcr.get())


def set_device_state(endpoint_id, value):
    """
    Update the shadow state for a device, and wait for it to change
    """
    response = aws_iot.update_thing_shadow(
        thingName=endpoint_id,
        payload=json.dumps({
            'state': {
                'desired': {
                    'state': value
                }
            }
        })
    )
    if response is None:
        return

    # wait for the reported state to change
    timeout = time.time() + 5
    while time.time() < timeout:
        time.sleep(0.25)
        try:
            shadow = json.load(aws_iot.get_thing_shadow(thingName=endpoint_id)['payload'])
            if shadow['state']['reported']['state'] == value:
                return True
        except:
            pass

    return False


_ACTIONS = {
    'Alexa.Discovery': discover_devices,
    'Alexa.PowerController': control_device
}


def is_valid_payload_version(request):
    """
    Check the API version in the request
    """
    payload_version = request['directive']['header']['payloadVersion']
    return payload_version == '3'


def lambda_handler(request, context):
    """
    Entry point
    """
    logger.debug(f'lambda_handler request {json.dumps(request)}')
    logger.debug(f'lambda_handler context {context}')

    if 'directive' not in request:
        return error(type='INVALID_DIRECTIVE', message='Missing key: directive, Is the request a valid Alexa Directive?')

    if not is_valid_payload_version(request):
        return error(type='INTERNAL_ERROR', message='This skill only supports Smart Home API version 3')

    name = request['directive']['header']['name']
    namespace = request['directive']['header']['namespace']

    return _ACTIONS[namespace](request)

