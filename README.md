# Velux Window Controller

We have a room at the back of the house with two electrically operated
Velux windows in the roof, about four metres above the floor. Since they
were installed I've been controlling them with Alexa and a Raspberry Pi
set up to electrically "push" the buttons on the window remote.

The Raspberry Pi was originally running some Python code I wrote based
on [fauxmo](https://github.com/makermusings/fauxmo), but this has 
increasingly been unreliable as Alexa has evolved and recently stopped
working altogether. So I rebuilt the system using the official SDKs and
toolkits.

There are several components:
* An [Alexa Smart Home skill](https://developer.amazon.com/alexa/connected-devices)
* The skill has account linking enabled using [Login With Amazon](https://login.amazon.com/website)
* The skill invokes an [AWS Lambda](https://aws.amazon.com/lambda/) function for device discovery and control
* The Lambda function updates the state for an [AWS IoT Core](https://aws.amazon.com/iot-core/) device
* The Raspberry Pi runs a simple script which subscribes and acts on changes to the state in IoT core



