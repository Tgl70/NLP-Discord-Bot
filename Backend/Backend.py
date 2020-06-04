#!/usr/bin/env python3
import requests
import json
import copy

from datetime import datetime
import cherrypy

from FSM import FSM
from utils import *
from config import *
from LogConversation import Logger


class Backend(object):
    def __init__(s):
        s.fsm = FSM()
        s.logger = Logger(LOGS_FOLDERPATH)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def index(s):
        alana_msg = s.getAlanaMessage()
        s.printAlanaMessage(alana_msg, fullJsonDisplay=True)

        # Init response object
        resp_to_alana = copy.deepcopy(BOT_TO_ALANA_PAYLOAD)
        resp_to_alana["bot_params"] = {"time": str(datetime.now())}

        session_id = alana_msg["current_state"]["session_id"]

        if session_id not in s.fsm.game_states.keys():
            s.fsm.game_states[session_id] = GameState()
            s.logger.log_new_game(session_id, s.fsm.game_states[session_id].game_id)

        s.logger.log_game_id(s.fsm.game_states[session_id].game_id)
        s.logger.log_user_message(alana_msg["current_state"]["state"]["input"]["text"])

        game_state = s.fsm.game_states[session_id]

        ########################### SET VOICE ###########################
        if game_state.talking_to == "bartender":
            resp_to_alana["bot_params"]["voice"] = "en-US_LisaVoice"
        elif game_state.talking_to == "villager":
            resp_to_alana["bot_params"]["voice"] = "en-US_MichaelVoice"
        else:
            resp_to_alana["bot_params"]["voice"] = "en-US_AllisonVoice"
        ########################### SET VOICE ###########################

        if not game_state.map_data and alana_msg["current_state"]["state"]["input"]["text"] == "start_game":
            resp_to_alana["result"] = s.fsm.start_game(game_state, option="open")

        elif not game_state.map_data and alana_msg["current_state"]["state"]["input"]["text"] == "start_game_close":
            resp_to_alana["result"] = s.fsm.start_game(game_state, option="close")

        elif not game_state.map_data and alana_msg["current_state"]["state"]["input"]["text"] == "start_game_gpt2":
            resp_to_alana["result"] = s.fsm.start_game(game_state, option="gpt2")

        elif not game_state.map_data:
            resp_to_alana["bot_params"]["game_exist"] = False
            resp_to_alana["result"] = "THIS STRING SHOULD NOT BE DISPLAYED (NO MAP DATA EDGECASE)"

        elif alana_msg["current_state"]["state"]["input"]["text"] == f"end_game_{session_id}":
            resp_to_alana["result"] = s.fsm.end_game(game_state, "close")

        else:
            rasa_resp = s.getRasaNLU(alana_msg)
            s.logger.log_rasa_confidence(rasa_resp["intent"])

            colorPrint(f"{'-'*20}\nEntities detected:", GREEN)
            print(json.dumps(rasa_resp["entities"], indent=4, sort_keys=True))
            colorPrint(f"{'-' * 20}\nIntents detected:", GREEN)
            print(json.dumps(rasa_resp["intent"], indent=4, sort_keys=True))

            # Update EMOTION SCORE every time the player talks to an NPC
            if game_state.game_mode != "gpt2" and game_state.talking_to != "Game_master":
                sentiment_analysis = alana_msg["current_state"]["state"]["nlu"]["annotations"]["sentiment"]

                # Special case for the VILLAGER
                if game_state.talking_to == "villager" and rasa_resp and rasa_resp["intent"]["name"] == "buy_drink":
                    sentiment_analysis["compound"] = 1.

                s.fsm.update_emotion_score(game_state, sentiment_analysis)

            if rasa_resp and rasa_resp["intent"]["confidence"] > 0.4:
                intent = rasa_resp["intent"]["name"]
                params = rasa_resp["entities"]

                # This helps to RECOGNISE NAMES when Rasa fails at that labor
                if intent == "inform_name" and not params and\
                        "ner" in alana_msg["current_state"]["state"]["nlu"]["annotations"].keys() and\
                        "PERSON" in alana_msg["current_state"]["state"]["nlu"]["annotations"]["ner"].keys():

                    names = alana_msg["current_state"]["state"]["nlu"]["annotations"]["ner"]["PERSON"]
                    if names:
                        name = {"entity": "name", "value": names[0]}
                        params.append(name)

                ########################### JUST GPT-2 ###########################
                if game_state.game_mode == "gpt2" and "nps" in alana_msg["current_state"]["state"]["nlu"]["annotations"].keys():
                    nouns = alana_msg["current_state"]["state"]["nlu"]["annotations"]["nps"]
                    for noun in nouns:
                        if all(noun.lower() != param["value"].lower() for param in params):  # Noun does not exist in params
                            if intent == "attack":  # It's with the only intent that we check the entity type
                                entity = {"entity": "npc", "value": noun}
                            else:
                                entity = {"entity": "", "value": noun}
                            params.append(entity)
                ########################### JUST GPT-2 ###########################
                resp_to_alana["result"] = s.fsm.update(game_state, intent, params)

            # Generate FALLBACK reply when talking to game master but no intent detected with enough confidence
            elif game_state.talking_to == "Game_master":
                game_state.pending_action = ""
                resp_to_alana["result"] = s.fsm.gm_NLG.fallback_response()

            # NEXT IFS WILL ONLY APPLY TO NPCs
            # In case the player does chit-chat for more than 3 turns
            elif game_state.misleading_turns >= 3:
                resp_to_alana["result"] = s.fsm.npc_NLG.action(game_state, intent="force_back")
            else: game_state.misleading_turns += 1

        if not resp_to_alana["result"]:
            colorPrint(f"{'-' * 20}\nNo intent detected. Sending emtpy string to Alana:", RED)
            resp_to_alana["result"] = ""  # Send empty response will make Alana choose the answer from the next bot in the priority list
        else:
            resp_to_alana["lock_requested"] = True  # We want Alana to choose the answer from our bot if it actually produced one
            colorPrint(f"{'-'*20}\nResponse detected. Sending back to Alana:", GREEN)
            print(resp_to_alana["result"])

        ########################### SET NAME ###########################
        if game_state.talking_to == "bartender":
            resp_to_alana["bot_params"]["name"] = "Bartender"
        elif game_state.talking_to == "villager":
            resp_to_alana["bot_params"]["name"] = "Drunk villager"
        else:
            resp_to_alana["bot_params"]["name"] = "Game Master"
        ########################### SET NAME ###########################

        resp_to_alana["bot_params"]["over"] = game_state.is_over

        s.logger.log_bot_response(resp_to_alana["result"])
        s.logger.log_flush()
        if game_state.is_over:
            s.logger.log_end_game(session_id, game_state.game_id, game_state)
            game_state.__init__()

        return json.dumps([resp_to_alana])

    def getRasaNLU(s, alana_msg):
        rasa_msg = {
          "text": alana_msg["current_state"]["state"]["input"]["text"]
        }
        print(f"{GREEN}{'-'*20}\nSending to Rasa on {RESET}{RASA_NLU_ENDPOINT}:")
        print(json.dumps(rasa_msg, indent=4, sort_keys=True))

        # Send the user message to the rasa server
        try:
            rasa_resp = requests.post(RASA_NLU_ENDPOINT, data=json.dumps(rasa_msg))
        except:
            colorPrint(f"{'-'*20}\nConnection to rasa server failed", RED)
        else:
            if rasa_resp.status_code != requests.codes.ok:
                print(f"{RED}{'-'*20}\nRequest to rasa failed:{RESET} {rasa_resp.status_code}")
            elif rasa_resp.headers.get('content-type') != 'application/json':
                colorPrint(f"{'-'*20}\nMalformed rasa response (not JSON)", RED)
            else:
                return rasa_resp.json()

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
            # for key, item in alana_msg.items():
                # print(f"{'-'*20}\n{key}:\t{item}")
        else:
            sender = alana_msg["current_state"]["session_id"]
            message = alana_msg["current_state"]["state"]["input"]["text"]
            print(f"{'-'*40}{GREEN}\n{'-'*30}\nMessage received from {RESET}{sender}:\n-> {message}")


if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': SERVER_IP,
        'server.socket_port': SERVER_PORT
    })
    cherrypy.quickstart(Backend(), '/')
