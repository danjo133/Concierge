from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from flask import Flask, jsonify, request, make_response
import os
import time
import configparser

config = configparser.ConfigParser()
config.read("config.cfg")
if config["Hue"]:
    huehost = config["Hue"]["HOST"]
else:
    print("Missing Hue config")
    exit(1)

        
from phue import Bridge

def processRequest(req):
    result = req.get('result')
    if result is None:
        return {}
    parameters = result.get('parameters')
    if parameters is None:
        return {}
    state = parameters.get('LightState')
    if state is None:
        return {}

    speech = ""
    b = Bridge(huehost)
    b.connect()
    #b.get_api()

    # Should take groupname into account when deciding on which lamp to turn on
    # b.get_group()
    if state == "on" or state == "On":
        if not b.get_light(1,'on'):
            b.set_light(1,'on',True)
            b.set_light(1,'bri',254)
            speech = "Turned lamp on"
        else:
            speech = "Lamp was already on."
    elif state == "off" or state == "Off":
        if b.get_light(1,'on'):
            b.set_light(1,'on',False)
            speech = "Turned lamp off"
        else:
            speech = "Lamp was already off"

    else:
        speech = "I couldn't understand the lampstate: " + state

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-hue-webhook"
    }
