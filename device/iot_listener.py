#!/usr/bin/env python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from fresh_air import WindowController
import logging
import time
import json


host = "aa40w08kkflrp-ats.iot.eu-west-1.amazonaws.com"
port = 443
rootCAPath = "./root-CA.crt"
thingName = "fresh-air"
clientId = "fresh-air-buttons"

logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


def shadow_callback(window_controller):
    def callback(payload, responseStatus, token):
        if json.loads(payload)["state"]["state"] == "ON":
            window_controller.open_windows()
        else:
            window_controller.close_windows()
    
    return callback


def create_iot():
    iot = AWSIoTMQTTShadowClient(clientId, useWebsocket=True)
    iot.configureEndpoint(host, port)
    iot.configureCredentials(rootCAPath)
    iot.configureAutoReconnectBackoffTime(1, 32, 20)
    iot.configureConnectDisconnectTimeout(10) 
    iot.configureMQTTOperationTimeout(5)
    iot.connect()
    return iot


def create_shadow_handler(iot, callback):
    handler = iot.createShadowHandlerWithName(thingName, True)
    handler.shadowRegisterDeltaCallback(callback)


if __name__ == "__main__":
    with WindowController() as window_controller:
        iot = create_iot()
        create_shadow_handler(iot, shadow_callback(window_controller))

        while True:
            time.sleep(1)
