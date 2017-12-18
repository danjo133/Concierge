#!/usr/bin/python3

import json
import os.path
import sys
import _thread
import time
import configparser

# from urllib.parse import urlparse, urlencode
# from urllib.request import urlopen, Request
# from urllib.error import HTTPError

from flask import Flask, jsonify, request, make_response
import requests

try:
    from apiai import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

import weather
import awesomethings
import huecontroller
import mongoquotes


hooks = dict(
    [
        ("yahooWeatherForecast", weather.process_request),
        ("awesomethings", awesomethings.process_request),
        ("controllights", huecontroller.process_request),
        ("storequotes", mongoquotes.process_request),
        ("readquotes", mongoquotes.process_request)
     ])


debug = True
jsondebug = True
dothread = False


def debug_printjson(*args):
    if jsondebug:
        print(args)


def debug_print(*args):
    if debug:
        print(args)


# apiai client access token
APIAI_CLIENT_ACCESS_TOKEN = ''

ai = None

# facebook client access token
FACEBOOK_CLIENT_ACCESS_TOKEN = ''

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
print(ASSETS_DIR)

# Will hold secrets that are required to communicate with this webapp
allowed_services = {}
# Will hold known users
userid = {}


# Used to verify that the service is valid (typically facebook or api.ai) and that the request
# has supplied a valid password
def verify_service(req):
    service = req.headers.get('service')
    secret = req.headers.get('secret')
    if service not in allowed_services or secret != allowed_services[service]:
        return False
    print("Valid credentials supplied, this is an authorized service")
    return True


# Just a debug thing so you can verify that the webserver is listening
@app.route('/')
def index():
    return 'Hi there.'


# Not used, only a minimal request/reply thing you can use to test out that you can send encrypted secrets
# and get the webserver to reply with json
@app.route('/testjson')
def names():
    if not verify_service(request):
        return "Invalid credentials"
    data = {"names": ["Covfefe", "Doge", "Trollface", "Grumpy Cat"]}
    return jsonify(data)


# Entrypoint for calls coming from API.ai
@app.route('/apiai_webhook', methods=['POST'])
def apiai_webhook():
    start = time.time()
    if not verify_service(request):
        return "Invalid credentials"
    req = request.get_json(silent=True, force=True)
    debug_printjson("Request:")
    debug_printjson(json.dumps(req, indent=4))
    res = {}

    action = req.get("result").get("action")
    if action is None:
        return {}

    if action in hooks:
        res = hooks[action](req)

    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    end = time.time()
    debug_print("Apiai webhook total time: " + str(end-start))
    return r


def facebook_reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    resp = requests.post(
        "https://graph.facebook.com/v2.6/me/messages?access_token=" + FACEBOOK_CLIENT_ACCESS_TOKEN, json=data
    )
    # print("Sent message to facebook: " + resp.content)
    debug_print(resp.content)


def facebook_apiai(threadname, message):
    start = time.time()
    response = send_apiai_request(userid["apiai"], message)
    endapiaitime = time.time()
    json_obj = json.loads(response)
    jsonparsingtime = time.time()
    debug_printjson(json.dumps(json_obj, indent=4))
    facebook_reply(userid["facebook"], json_obj["result"]["fulfillment"]["messages"][0]["speech"])
    endfacebookreply = time.time()
    debug_print(
        "threadname: " + threadname +
        "apiaireq: " + str(endapiaitime-start) + ", " +
        "jsonparsing: " + str(jsonparsingtime-endapiaitime) + ", " +
        "facebookreplytime: " + str(endfacebookreply-jsonparsingtime)
        )


# Entrypoint for calls coming from Facebook
@app.route('/facebook_webhook', methods=['POST', 'GET'])
def facebook_webhook():

    startwebhook = time.time()

    # Deal with facebook making sure you are in control of the host
    if request.method == 'GET' and request.args['hub.mode'] == "subscribe":
        print("Subscription request")
        if request.args['hub.verify_token'] == allowed_services["facebook"]:
            return request.args['hub.challenge']
        else:
            print("Invalid subscription")
            return ""

    # Deal with message sent from facebook

    data = request.json
    
    startdataparsing = time.time()
    
    if not data:
        print("Bad request")
        print(request)
        return "ok"

    if "entry" not in data:
        print("No entry part in data")
        print(data)
        return "ok"

    entry = data['entry'][0]

    if "messaging" not in entry:
        print("No messaging part in entry")
        print(entry)
        return "ok"
        
    messaging = entry["messaging"][0]
    sender = messaging['sender']['id']
    message = messaging['message']['text']

    debug_printjson("Request:")
    debug_printjson(json.dumps(data, indent=4))

    enddataparsing = time.time()

    startapiaithread = 0
    endapiaithread = 0
    startfacebookreply = 0
    endfacebookreply = 0

    if sender == userid["facebook"]:
        # We only do processing on messages coming from the specified user

        # Possibility to do threaded/async queries to apiai
        if dothread:
            startapiaithread = time.time()
            _thread.start_new_thread(facebook_apiai, ("ApiAi-Thread-1", message))
            endapiaithread = time.time()
            message = "Ok, deferring to APIAI, Will be back momentarily!"

            startfacebookreply = time.time()
        
            facebook_reply(sender, message)

            endfacebookreply = time.time()
        else:
            facebook_apiai("ApiAI-Thread-1", message)
        
    else:
        # All other users just get their own messages echoed back reversed
        facebook_reply(sender, message[::-1])

    debug_print(
        "Subscription: " + str(startdataparsing-startwebhook) + ", " +
        "Dataparsing: " + str(enddataparsing-startdataparsing) + ", " +
        "Apiai thread: " + str(endapiaithread-startapiaithread) + ", " +
        "Facebook reply: " + str(endfacebookreply-startfacebookreply)
    )
    
    return "ok"


def send_apiai_request(user_id, query):
    start = time.time()

    endinit = time.time()

    apirequest = ai.text_request()

    apirequest.lang = 'en'  # optional, default value equal 'en'

    apirequest.session_id = user_id
    apirequest.query = query

    endrequestcreation = time.time()
    
    apiresponse = apirequest.getresponse()

    gotresponsetime = time.time()

    print("APIAI response: ")
    response_string = apiresponse.read().decode("utf-8")

    debug_printjson(response_string)
    debug_print(
        "InitApiai: " + str(endinit-start) + ", " +
        "End req creation: " + str(endrequestcreation - endinit) + ", " +
        "Response time: " + str(gotresponsetime-endrequestcreation)
    )

    return response_string


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.cfg")
    if not config["Concierge"]: 
        print("Bad config, no Concierge block found")
        exit(1)
       
    if config["Concierge"]["PORT"]:
        port = int(config["Concierge"]["PORT"])
    else:
        port = int(os.getenv('PORT', 5000))

    if config["Concierge"]["HOST"]:
        host = config["Concierge"]["HOST"]
    else:
        host = "192.168.1.1"

    sslcert = ""
    if config["Concierge"]["CERT"]:
        sslcert = config["Concierge"]["CERT"]
    else:
        exit(1)

    sslkey = ""
    if config["Concierge"]["KEY"]:
        sslkey = config["Concierge"]["KEY"]
    else:
        exit(1)
        
    if config["Concierge"]["APIAI_CLIENT_ACCESS_TOKEN"]:
        APIAI_CLIENT_ACCESS_TOKEN = config["Concierge"]["APIAI_CLIENT_ACCESS_TOKEN"]
    else:
        print("No APIAI Token in config file")
        exit(1)

    if config["Concierge"]["FACEBOOK_CLIENT_ACCESS_TOKEN"]:
        FACEBOOK_CLIENT_ACCESS_TOKEN = config["Concierge"]["FACEBOOK_CLIENT_ACCESS_TOKEN"]
    else:
        print("No Facebook Token in config file")
        exit(1)

    if config["AllowedServices"]:
        for key in config["AllowedServices"]:
            allowed_services[key] = config["AllowedServices"][key]
    if config["UserId"]:
        for key in config["UserId"]:
            userid[key] = config["UserId"][key]

    ai = apiai.ApiAI(APIAI_CLIENT_ACCESS_TOKEN)

    context = (sslcert, sslkey)

    # Threading is very important since this webserver is hit twice,
    # once when coming from client and then again when returning from
    # api.ai
    app.run(debug=True, port=port, host=host, ssl_context=context, threaded=True)
