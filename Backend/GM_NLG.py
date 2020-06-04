#!/usr/bin/env python3
import json
import os.path
from config import *
from utils import *
import random


class GM_NLG:

    def __init__(self):
        if not os.path.isfile(GM_RESP_FILEPATH):
            colorPrint(f"FSM: Could not load game master responses data file (file not found)", RED)
            exit(1)

        with open(GM_RESP_FILEPATH, 'r') as f:
            self.responses = json.load(f)

    def start_game(self):
        return random.choice(self.responses["start_game"])

    def end_game(self, option):
        return random.choice(self.responses["end_game"][option])

    def move_to(self, option, location=None):
        res = random.choice(self.responses["move_to"][option])
        return res.format(loc=location)

    def get_description(self, location):
        return self.responses["descriptions"][location]

    def pick_up_object(self, option, obj=None, action=None):
        res = random.choice(self.responses["pick_up_object"][option])
        return res.format(object=obj, action=action)

    def talk_to_npc(self, npc, option=None):
        return random.choice(self.responses["talk_to_npc"][npc]) if not option \
            else random.choice(self.responses["talk_to_npc"][npc][option])

    def explore(self, variant, level=None, param1=None, param2="interact"):
        res = random.choice(self.responses["explore"][variant]) if not level \
            else random.choice(self.responses["explore"][variant][level])
        return res.format(param=param1, interaction=param2)

    def get_position_info(self, players_name="", location="world"):
        res = random.choice(self.responses["get_position_info"])
        return res.format(loc=location, name=players_name)

    def get_inventory_info(self, option, obj=None, action=None):
        res = random.choice(self.responses["get_inventory_info"][option])
        return res.format(object=obj, action=action)

    def get_player_info(self, players_name="", health=21):
        res = random.choice(self.responses["get_player_info"])
        return res.format(health=health, name=players_name)

    def inform_name(self, option, players_name=""):
        res = random.choice(self.responses["inform_name"][option])
        return res.format(name=players_name)

    def thanking(self, players_name=""):
        res = random.choice(self.responses["thanking"])
        return res.format(name=players_name)

    def greeting(self, option, players_name=""):
        res = random.choice(self.responses["greeting"][option])
        return res.format(name=players_name)

    def farewell(self):
        return random.choice(self.responses["farewell"]["ask_end_game"])

    def cancelling_action(self):
        return random.choice(self.responses["cancelling_action"])

    def pending(self, action):
        return random.choice(self.responses[action]["pending"])

    def pending_fallback(self):
        return random.choice(self.responses["pending_fallback"])

    def fallback_response(self):
        return random.choice(self.responses["fallback_response"])

    def gpt2_intro(self, location):
        return random.choice(self.responses["gpt2_intros"]).format(location=location)
