from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from flask import Flask, jsonify, request, make_response
import os


def processRequest(req):
    res = makeWebhookResult(req)
    return res

def makeWebhookResult(data):
    result = data.get('result')
    if result is None:
        return {}
    parameters = result.get('parameters')
    if parameters is None:
        return {}
    thing = parameters.get('given-name')
    if thing is None:
        return {}
    awesomethings = { 'Apple' : 'not so awesome..',
                      'Monkey' : 'So Awesome!',
                      'Carburetor' : "Now you're just trolling.."
    }
 
    speech = "Hi there, I'm glad you asked, " + thing + " is "
    if thing in awesomethings:
        speech += awesomethings[thing]
    else:
        speech += " ... what is that again?"

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-awesomethings-webhook"
    }
