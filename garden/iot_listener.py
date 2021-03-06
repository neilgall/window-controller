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

        @logger.log_with(_LOG, device=thing_name)
        def do_update(state):
            value = "ON" if state else "OFF"
            shadow.shadowUpdate(json.dumps({ "state": { "reported": { "state": value } } }), None, 5)

        @logger.log_with(_LOG, device=thing_name)
        def on_get(payload, response_status, token):
            state = json.loads(payload)['state']['desired']['state']
            if state in ['ON', 'OFF']:
                handler(state == "ON")

        @logger.log_with(_LOG, device=thing_name)
        def on_delta(payload, response_status, token):
            state = json.loads(payload)['state']['state']
            if state in ['ON', 'OFF']:
                handler(state == "ON")

        shadow.shadowGet(on_get, 5)
        shadow.shadowRegisterDeltaCallback(on_delta)
        return do_update


class DeviceAdapter:
    def __init__(self, endpoint, name, garden_controller):
        self._endpoint = str(endpoint)
        self._name = str(name)
        self._garden_controller = garden_controller
        self._update_hook = None

    def __repr__(self):
        return f'DeviceAdapter[{endpoint}]'

    @logger.log_with(_LOG)
    def set_update_hook(self, hook):
        self._update_hook = hook

    @logger.log_with(_LOG)
    def shadow_to_device(self, state):
        if state:
            self._garden_controller.lights_on(self._endpoint)
        else:
            self._garden_controller.lights_off(self._endpoint)

    @logger.log_with(_LOG)
    def device_to_shadow(self, state):
        pushover.send(_CLIENT_NAME, f"{self._name} {'on' if state else 'off'}!")
        self._update_hook(state)


if __name__ == "__main__":
    with GardenController() as garden_controller:
        iot = IoTCoreClient()

        for endpoint, zone in garden_controller.get_zones().items():
            friendly_name = zone['friendly_name']
            adapter = DeviceAdapter(endpoint, friendly_name, garden_controller)
            shadow_update = iot.create_shadow_handler(endpoint, adapter.shadow_to_device)
            adapter.set_update_hook(shadow_update)
            garden_controller.set_update_hook(endpoint, adapter.device_to_shadow)

            _LOG.info(f"Created handler for {friendly_name}")

        pushover.send(_CLIENT_ID, "Listener started")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
