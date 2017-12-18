# What is this?
This is a work in progress virtual assistant named concierge.
It is a python backend to a facebook frontend where you can do whatever you want with the input coming from facebook.
It also passes the facebook text through api.ai to tokenize it and receives the output from there so you can act on that.
Currently it only supports controlling Hue lights and returning some random text.

The phue.py file comes from https://github.com/studioimaginaire/phue and you may want to keep that updated.

# Usage
$ git clone https://github.com/danjo133/Concierge
$ cd Concierge
$ pip3 install -t apiai apiai
$ cp config.cfg.example config.cfg
# Edit config.cfg
$ ./app.py

# Website tips
https://dialogflow.com/ (previously api.ai)
http://www.girliemac.com/blog/2017/01/06/facebook-apiai-bot-nodejs/

Basically, you need to:
1) Setup your intent-mapping on dialogflow and connect it to this app
2) Setup a facebook page, create a bot for it, set it to send webhooks to this app
3) Store your API-keys in the config.cfg-file. config.cfg is in the .gitignore for a reason.