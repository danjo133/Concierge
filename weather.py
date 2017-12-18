from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
# from urllib.error import HTTPError

import json

# from flask import Flask, jsonify, request, make_response
# import os


def process_request(req):
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = make_yql_query(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read().decode("utf-8")
    data = json.loads(result)
    res = make_webhook_result(data)
    return res


def make_yql_query(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


# Convert Fahrenheit to Celsius, return with one decimal place
def f2c(f):
    return "{0:.1f}".format((float(f)-32)/(9/5))


def make_webhook_result(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    if units.get('temperature') == "F":
        speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
                 ", the temperature is " + f2c(condition.get('temp')) + " C"
    else:
        speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
                 ", the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }
