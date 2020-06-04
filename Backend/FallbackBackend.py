#!/usr/bin/env python3
import requests
import json
import copy
import random
from datetime import datetime

import cherrypy

from FSM import FSM
from utils import *
from config import *


class Backend(object):
    def __init__(s):
        s.fsm = FSM()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def index(s):
        alana_msg = s.getAlanaMessage()
        s.printAlanaMessage(alana_msg, fullJsonDisplay=True)

        # Init response object
        resp_to_alana = copy.deepcopy(BOT_TO_ALANA_PAYLOAD)
        resp_to_alana["bot_name"] = FALLBACK_BOT_NAME
        resp_to_alana["bot_params"] = {"time": str(datetime.now())}

        fallback_responses = [
            "Did you know this village used to be center for all transportation and mining operations in the region? And look how we are now.",
            "Just look around you, this inn should be crowded at this time of the day.",
            "This village had't suffered a threat as this one in years.",
            "The world is full of magical things patiently waiting for our wits to grow sharper.",
            "We'll get through this. I'm sure of that.",
            "You know what's wrong with this village these days? Everyone is obsessed with death.",
            "I used to be an adventurer like you. Then I took an arrow in the knee.",
            "Never should have come here!",
            "You picked a bad time to get lost, friend!",
            "Change, change will preserve us. It will move mountains, it will mount movements.",
            "I've been hunting and fishing in these parts for years."
        ]

        resp_to_alana["result"] = random.choice(fallback_responses)
        return json.dumps([resp_to_alana])

    def getAlanaMessage(s):
        try:
            alana_msg = cherrypy.request.json
        except AttributeError:
            colorPrint("Invalid query (no JSON)", RED)
            return {"result": "Invalid query (no JSON)"}

        return alana_msg

    def printAlanaMessage(s, alana_msg, fullJsonDisplay=False):
        if fullJsonDisplay:
            colorPrint(f"\n{'-'*40}\n{'-'*40}\nReceived from Alana:", GREEN)
            print(json.dumps(alana_msg["current_state"]["state"], indent=4, sort_keys=True))
        else:
            sender = alana_msg["current_state"]["session_id"]
            message = alana_msg["current_state"]["state"]["input"]["text"]
            print(f"{'-'*40}{GREEN}\n{'-'*30}\nMessage received from {RESET}{sender}:\n-> {message}")


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': SERVER_IP,
        'server.socket_port': FALLBACK_SERVER_PORT
    })
    cherrypy.quickstart(Backend(), '/')
