#!/usr/bin/env python
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from garden_controller import GardenController
import logging
import json
import pushover
import time


host = "aa40w08kkflrp-ats.iot.eu-west-1.amazonaws.com"
port = 443
rootCAPath = "./root-CA.crt"
thingName = "garden-lights"
clientId = "garden-lights-controller"

logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


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
    shadow = iot.createShadowHandlerWithName(thingName, True)

    def on_delta(payload, responseStatus, token):
        print(payload)
        state = json.loads(payload)["state"].get("state")
        if state is not None:
            callback(state == "ON")
            shadow.shadowUpdate(json.dumps({ "state": { "reported": { "state": state } } }), None, 5)

    shadow.shadowRegisterDeltaCallback(on_delta)


if __name__ == "__main__":
    with GardenController() as garden_controller:
        def callback(state):
            if state:
                garden_controller.lights_on()
                pushover.send("Garden Lights", "Lights on!")
            else:
                garden_controller.lights_off()
                pushover.send("Garden Lights", "Lights off!")
        
        create_shadow_handler(create_iot(), callback)

        while True:
            garden_controller.poll_switch()
            time.sleep(1)
