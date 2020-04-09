#!/usr/bin/env python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from garden_controller import GardenController
import logger
import json
import pushover
import time


_HOST = "aa40w08kkflrp-ats.iot.eu-west-1.amazonaws.com"
_PORT = 443
_ROOT_CA_PATH = "./root-CA.crt"
_CLIENT_ID = "garden-controller"
_CLIENT_NAME = "Garden Controller"

_DEVICES = [
    {
        'friendly_name': 'Fresh Air',
        'description': 'Windows in Family Room',
        'endpoint_id': 'fresh-air'
    },
    {
        'friendly_name': 'Summerhouse lights',
        'description': 'Internal lights in the summerhouse',
        'endpoint_id': 'summerhouse-lights'
    },
    {
        'friendly_name': 'Garden Fairy Lights',
        'description': 'Fairy Lights all around the Garden',
        'endpoint_id': 'garden-lights'    
    }
]

_LOG = logger.create("iot_listener", logger.INFO)
logger.create("AWSIoTPythonSDK.core", logger.WARN)


class IoTCoreClient:
    def __init__(self):
        self._iot = AWSIoTMQTTShadowClient(_CLIENT_ID, useWebsocket=True)
        self._iot.configureEndpoint(_HOST, _PORT)
        self._iot.configureCredentials(_ROOT_CA_PATH)
        self._iot.configureAutoReconnectBackoffTime(1, 32, 20)
        self._iot.configureConnectDisconnectTimeout(10) 
        self._iot.configureMQTTOperationTimeout(5)
        self._iot.connect()

    def create_shadow_handler(self, thing_name, handler):
        shadow = self._iot.createShadowHandlerWithName(thing_name, True)

        def on_delta(payload, response_status, token):
            state = json.loads(payload)["state"].get("state")
            if state is not None:
                real_state = handler(state == "ON")
                shadow.shadowUpdate(json.dumps({ "state": { "reported": { "state": real_state } } }), None, 5)

        shadow.shadowRegisterDeltaCallback(on_delta)


if __name__ == "__main__":
    with GardenController() as garden_controller:
        iot = IoTCoreClient()

        for device in _DEVICES:
            def callback(state):
                if state:
                    garden_controller.lights_on(device['endpoint_id'])
                    pushover.send(_CLIENT_NAME, f"{device['friendly_name']} on!")
                else:
                    garden_controller.lights_off(device['endpoint_id'])
                    pushover.send(_CLIENT_NAME, f"{device['friendly_name']} off!")
                return state
        
            iot.create_shadow_handler(device['endpoint_id'], callback)
            _LOG.info(f"Createed handler for {device['friendly_name']}")

        pushover.send(_CLIENT_ID, "Listener started")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
