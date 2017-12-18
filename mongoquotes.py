# Note, this code is under development and untested since newer versions of MongoDB requires 64bit OS and RaspberryPi only has 32bit OSes.

# For webserver
# from urllib.parse import urlparse, urlencode
# from urllib.request import urlopen, Request
# from urllib.error import HTTPError

# from flask import Flask, jsonify, request, make_response
# import os

import configparser
import random

# For mongodb
from pymongo import MongoClient
import datetime

config = configparser.ConfigParser()
config.read("config.cfg")
if not config["MongoDB"]:
    print("Missing MongoDB config")
    exit(1)

mongohost = config["MongoDB"]["HOST"]
mongoport = int(config["MongoDB"]["PORT"])


def get_parameters(req):
    result = req.get('result')
    if result is None:
        return {}
    parameters = result.get('parameters')
    if parameters is None:
        return {}
    return parameters


def get_action(req):
    result = req.get('result')
    if result is None:
        return {}

    action = result.get('action')
    if action is None:
        return ""

    return action


def process_request(req):
    client = MongoClient(mongohost, mongoport)
    db = client.concierge
    collection = db.stored_quotes

    action = get_action(req)
    parameters = get_parameters(req)
    print("Processing request")

    if action is None:
        return {}

    if action == "storequotes":
        print("Storing quote")
        quote = parameters.get('quote')
        if quote is None:
            return {}
        post = {"author": "Daniel", "text": quote, "date": datetime.datetime.utcnow(), "category": "dumber"}
        collection.insert(post)

        return {
            "speech": "Added quote to database",
            "displayText": "Added quote to database",
            # "data": data,
            # "contextOut": [],
            "source": "apiai-webhook"
        }
    if action == "readquotes":
        print("Reading quotes")
        name = parameters.get('given-name')
        output = {}
        if name is None:
            output = collection.find_one()
        elif name == "random":
            count = collection.count()
            output = collection.find()[random.randrange(count)]
            # output = collection.find_one()
        else:
            output = collection.find_one({"author": name})
        res = make_webhook_result(output)
        return res

    print(action)
    return {}


def make_webhook_result(data):
    if "author" in data and "text" in data:
        speech = "Hi, here's a quote from " + data['author'] + ": " + data["text"]
    else:
        speech = "Hi, no good quotes available."

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-webhook"
    }
