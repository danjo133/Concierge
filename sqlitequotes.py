# from urllib.parse import urlparse, urlencode
# from urllib.request import urlopen, Request
# from urllib.error import HTTPError

# from flask import Flask, jsonify, request, make_response
# import os

import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


connection = sqlite3.connect("quotes.db")
connection.row_factory = dict_factory

cursor = connection.cursor()

cursor.execute("select * from sample")

# fetch all or one we'll go for all.

results = cursor.fetchall()
print(results)

connection.close()


def process_request(req):
    res = make_webhook_result(req)
    return res


def make_webhook_result(data):
    result = data.get('result')
    if result is None:
        return {}
    parameters = result.get('parameters')
    if parameters is None:
        return {}
    thing = parameters.get('given-name')
    if thing is None:
        return {}
    awesomethings = {'Apple': 'not so awesome..',
                     'Monkey': 'So Awesome!',
                     'Carburetor': "Now you're just trolling.."
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
