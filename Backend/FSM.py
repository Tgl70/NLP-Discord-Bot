#!/usr/bin/env python3
import json
import os.path

from GM_NLG import *
from NPCsDialogManager import *
from GPT2Interface import *
from utils import *
from config import *


class FSM(object):
    def __init__(s):

        s.game_states = {}

        s.gm_NLG = GM_NLG()
        s.npc_NLG = NPCsDialogManager()
        s.gpt2 = GPT2Interface()

        s.intents_functions = {
            "greet": "greet",
            "farewell": "farewell",
            "affirm": "affirm",
            "deny": "deny",
            "thanking": "thanking",
            "move_to": "move_to",
            "attack": "attack",
            "inform_name": "inform_name",
            "pick_up_object": "pick_up_object",
            "talk_to_npc": "talk_to_npc",
            "explore": "explore",
            "get_position_info" : "get_position_info",
            "get_inventory_info" : "get_inventory_info",
            "get_player_info" : "get_player_info",
        }

        s.pending_actions_intents = {
            "greeting": ["inform_name"],
            "farewell": ["affirm", "deny"]
        }

    def update(s, game_state, intent, params):
        if not game_state.map_data:
            colorPrint(f"""FSM: Map not loaded correctly """, RED)

        data = {"intent": intent, "params": params, "response": ""}

        if game_state.pending_action != "" and intent not in s.pending_actions_intents.get(game_state.pending_action):
                data["response"] = s.gm_NLG.pending(action=game_state.pending_action)
                game_state.pending_action = ""
        else:
            func = s.intents_functions.get(intent, None)

            if game_state.talking_to == "Game_master":
                # This will happen for intents such as ask_info or buy_drink, that ONLY apply to the NPCs
                if intent not in s.intents_functions.keys():
                    data["response"] = s.gm_NLG.fallback_response()
                else:
                    func = "s." + func + "(game_state, params)"
            else:
                func = "s.npc_NLG.action" + "(game_state, intent)"
                game_state.nb_turn_npc += 1

            if not data["response"] and func:
                res = eval(func)
                if res:
                    data["response"] = res
                    # This will end the conversation with the NPCs
                    if intent == "farewell":
                        game_state.misleading_turns = 0
                        game_state.talking_to = "Game_master"

                # When talking to an NPC, if reply is empty --> Chit-chat --> Increase misleading_turns counter
                elif game_state.talking_to != "Game_master":
                    game_state.misleading_turns += 1
                else:
                    colorPrint(f"""FSM: Function "{intent}" did not return anything""", YELLOW)

            else:
                colorPrint(f"""FSM: Function not implemented yet for NPC {game_state.talking_to} | Intent: "{intent}" """, YELLOW)

        game_state.history.append(data)
        return data["response"]

    @staticmethod
    def update_emotion_score(game_state, sentiment_analysis):
        # EMOTION SCORE: -1 { Sad/Afraid/Negative } | 1 { Happy/Talkative/Positive }
        compound = sentiment_analysis["compound"]
        if compound != 0:
            game_state.emotion_score[game_state.talking_to] += compound
        elif sentiment_analysis["neu"] == 1:
            game_state.emotion_score[game_state.talking_to] += .5

    def greet(s, game_state, params):
        if game_state.player_name == "":
            game_state.pending_action = "greeting"
            return s.gm_NLG.greeting(option="asking_name")

        return s.gm_NLG.greeting(option="greeting", players_name=game_state.player_name)

    def farewell(s, game_state, params):
        game_state.pending_action = "farewell"
        return s.gm_NLG.farewell()

    def affirm(s, game_state, params):
        if game_state.pending_action == "farewell":
            res = s.end_game(game_state, "close")
        else:
            res = s.gm_NLG.pending_fallback()

        game_state.pending_action = ""
        return res

    def deny(s, game_state, params):
        if game_state.pending_action == "farewell":
            res = s.gm_NLG.cancelling_action()
        else:
            res = s.gm_NLG.pending_fallback()

        game_state.pending_action = ""
        return res

    def thanking(s, game_state, params):
        return s.gm_NLG.thanking(game_state.player_name)

    def move_to(s, game_state, params):
        if not params:
            return s.gm_NLG.move_to(option="no_location")

        ########################### JUST GPT-2 ###########################
        elif game_state.game_mode == "gpt2":
            colorPrint(f'MOVE_TO1 PARAMS: {params}', YELLOW)
            temp_params = []

            for entity in params:
                if any(item.lower().find(entity["value"].lower()) != -1 for item in game_state.knowledge):
                    for item in game_state.knowledge:
                        if item.lower().find(entity["value"].lower()) != -1:
                            entity["value"] = item
                            temp_params.append(entity)
                            break

                elif any(location.lower().find(entity["value"].lower()) != -1 for location in game_state.map_data["locations"][game_state.player_pos]["links"]):
                    for location in game_state.map_data["locations"][game_state.player_pos]["links"]:
                        if location.lower().find(entity["value"].lower()) != -1:
                            entity["value"] = location
                            temp_params.append(entity)
                            break

            params = temp_params
            colorPrint(f'MOVE_TO2 PARAMS: {params}', YELLOW)
            if not params: return s.gm_NLG.move_to(option="non_existing")
        ########################### JUST GPT-2 ###########################

        destination = params[0]["value"]

        if destination == game_state.player_pos:
            return s.gm_NLG.move_to(option="current")

        # If destination has already been visited there's no need to go through every other location
        if destination in game_state.knowledge:
            game_state.player_pos = destination

            if game_state.game_mode == "close":
                return s.gm_NLG.move_to(option="moving", location=destination) + "\n" + s.tell_options(game_state)

            return s.gm_NLG.move_to(option="moving", location=destination)

        if destination not in game_state.map_data['locations'].keys():

            ########################### JUST GPT-2 ###########################
            if game_state.game_mode == "gpt2" and destination in game_state.map_data["locations"][game_state.player_pos]["links"]:
                res, updated_map = s.gpt2.getGpt2Prediction(map_object=game_state.map_data,
                                                            come_from=game_state.player_pos,
                                                            place_name=destination,
                                                            input_text=s.gm_NLG.gpt2_intro(location=destination))
                game_state.player_pos = destination
                game_state.knowledge.append(destination)
                game_state.places_visited.append(destination)
                game_state.map_data = updated_map
                return res
            ########################### JUST GPT-2 ###########################

            return s.gm_NLG.move_to(option="non_existing")

        links = game_state.map_data["locations"][game_state.player_pos]["links"]
        destination_found_in_links = False

        for link in links:
            if destination == link:
                destination_found_in_links = True
                conditions = game_state.map_data["locations"][destination]["conditions"]
                if not conditions or all(condition in (game_state.knowledge + game_state.inventory) for condition in conditions):
                    if not destination in game_state.knowledge:
                        game_state.knowledge.append(destination)
                        game_state.places_visited.append(destination)
                    game_state.player_pos = destination
                    res = s.gm_NLG.move_to(option="moving", location=destination)

                    # Adding conditions satisfied to the response if there are any
                    for idx, condition in enumerate(conditions):
                        if idx == 0: res += f" using the {condition}"  # First condition
                        elif idx == len(conditions)-1: res += f" and the {condition}"  # Last condition
                        else: res += f", the {condition}"

                    if game_state.game_mode == "close":
                        res += "\n" + s.tell_options(game_state)
                    elif game_state.game_mode == "open":
                        res += s.gm_NLG.get_description(destination)

                    return res
                break

        if not destination_found_in_links:
            return s.gm_NLG.move_to(option="impossible", location=destination)
        else:  # Player does not satify the conditions
            return s.gm_NLG.move_to(option="inaccessible", location=destination)

    def attack(s, game_state, params):  # TODO: NLG IS MISSING HERE
        if not params:
            return s.gm_NLG.fallback_response()

        ########################### JUST GPT-2 ###########################
        elif game_state.game_mode == "gpt2":
            colorPrint(f'ATTACK PARAMS1: {params}', YELLOW)
            temp_params = []

            for entity in params:
                for npc in game_state.map_data["NPCs"].keys():
                    colorPrint(f'{npc.lower()} | {entity["value"].lower()} | {npc.lower().find(entity["value"].lower())}', YELLOW)
                    if npc.lower().find(entity["value"].lower()) != -1:
                        entity["entity"] = "npc"
                        entity["value"] = npc
                        temp_params.append(entity)
                        break

            params = temp_params
            colorPrint(f'ATTACK PARAMS2: {params}', YELLOW)
            if not params: return s.gm_NLG.fallback_response()
        ########################### JUST GPT-2 ###########################

        enemy = ""
        obj = ""
        damage = 3  # Default attack
        protection = 0

        # Define enemy and objects based on the entity params
        for entity in params:

            if entity["entity"] == "npc":
                # Check if enemy is present at current location
                if entity["value"] not in game_state.map_data["locations"][game_state.player_pos]["NPCs"]:
                    return f"There is no {entity['value']} here!"

                if enemy == "":
                    enemy = entity["value"]
                    # Check if we can attack the NPC
                    if "fight" not in game_state.map_data["NPCs"][enemy]["interactions"]:
                        return f"You cannot fight the {enemy}."

                else: return "You cannot attack more than one enemy at once."

            if entity["entity"] == "object":
                # Check if selected object is in your inventory
                if entity["value"] not in game_state.inventory:
                    return f"You don't have a {entity['value']} in your inventory"
                elif obj == "":
                    obj = entity["value"]
                    # Check if object can be used to attack
                    if "attack" not in game_state.map_data["objects"][obj]["interactions"]:
                        return "You cannot attack with this object"
                    # If you select the object with which you want to do the attack, you'll make the damage that object has assigned
                    damage = game_state.map_data["objects"][obj]["damage"]
                else: return "You cannot attack with more than two objects at once."

        # TODO: WHAT HAPPENS IF THERE'S NOT AN ENEMY ENTITY? (EXAMPLE: "I WILL KILL HIM")

        # If no object has been selected, check in the inventory for the object with the highest damage
        if obj == "":
            for item in game_state.inventory:
                if "attack" not in game_state.map_data["objects"][item]["interactions"]: continue  # Only look for objects that can be used to attack
                if game_state.map_data["objects"][item]["damage"] > damage: damage = game_state.map_data["objects"][item]["damage"]

        # Add protection value based on your items
        for item in game_state.inventory:
            protection += game_state.map_data["objects"][item]["protection"]

        # Player makes damage to the enemy
        game_state.map_data["NPCs"][enemy]["health"] -= damage
        if game_state.map_data["NPCs"][enemy]["health"] <= 0:

            if enemy == "monster":
                return s.end_game(game_state, "win")
            elif game_state.player_pos == "backyard" and enemy == "goblin":
                obj = "key"
                game_state.map_data["locations"][game_state.player_pos]["objects"].append(obj)  # Add key to the backyard once the goblin is dead
                game_state.map_data["locations"][game_state.player_pos]["NPCs"].remove(enemy)
                return f"Now that the {enemy} is dead you can take the {obj}."
            else:
                game_state.map_data["locations"][game_state.player_pos]["NPCs"].remove(enemy)
                return f"You killed the {enemy}"

        # Enemy makes damage to the player
        damage_to_player = game_state.map_data["NPCs"][enemy]["damage"] - protection
        game_state.map_data["player_info"]["health"] -= damage_to_player if damage_to_player > 0 else 0

        if game_state.map_data["player_info"]["health"] <= 0:
            return s.end_game(game_state, "lose")

        return f"You've caused {damage} of damage to the {enemy}, but it attacks back and " \
            f"deals {damage_to_player if damage_to_player > 0 else 0} of damage to you because you have a protection that's worth {protection} points."

    def inform_name(s, game_state, params):
        if game_state.pending_action == "greeting": game_state.pending_action = ""

        if not params:
            return s.gm_NLG.inform_name(option="no_name")

        if params[0]["entity"] == "name":
            if game_state.player_name == "":
                game_state.player_name = params[0]["value"]
                return s.gm_NLG.inform_name(option="first_time", players_name=game_state.player_name)
            else:
                game_state.player_name = params[0]["value"]
                return s.gm_NLG.inform_name(option="changing_name", players_name=game_state.player_name)

        return s.gm_NLG.inform_name(option="no_name")

    def pick_up_object(s, game_state, params):
        if not params:
            return s.gm_NLG.pick_up_object(option="no_objects")

        ########################### JUST GPT-2 ###########################
        elif game_state.game_mode == "gpt2":
            colorPrint(f'PICK_UP1 PARAMS: {params}', YELLOW)
            temp_params = []

            for entity in params:
                for obj in game_state.map_data["objects"].keys():
                    colorPrint(f'{obj.lower()} | {entity["value"].lower()} | {obj.lower().find(entity["value"].lower())}', YELLOW)
                    if obj.lower().find(entity["value"].lower()) != -1:
                        entity["value"] = obj
                        temp_params.append(entity)
                        break

            params = temp_params
            colorPrint(f'PICK_UP2 PARAMS: {params}', YELLOW)
            if not params: return s.gm_NLG.pick_up_object(option="no_objects")
        ########################### JUST GPT-2 ###########################

        if len(params) > 1:
            return "You can only take one object at a time"

        obj = params[0]["value"]
        # Check if object exists at the current location
        if obj not in game_state.map_data["locations"][game_state.player_pos]["objects"]:
            return s.gm_NLG.pick_up_object(option="non_existing", obj=obj)

        # Check if player can pick up the object
        if "pick_up" not in game_state.map_data["objects"][obj]["interactions"]:
            return s.gm_NLG.pick_up_object(option="impossible", obj=obj)

        game_state.inventory.append(obj)
        game_state.map_data["locations"][game_state.player_pos]["objects"].remove(obj)
        return s.gm_NLG.pick_up_object(option="grabbing", obj=obj, action=game_state.map_data["objects"][obj]["action"])

    # Switch from narrator to NPC. Following interactions will be with the NPC. Create a variable to define who the player is talking to.
    def talk_to_npc(s, game_state, params):
        if game_state.game_mode == "gpt2": return "Talking with NPCs is not possible in this version yet."

        if not params:
            return s.gm_NLG.talk_to_npc(npc="no_npc")

        npc = params[0]["value"]

        if npc not in game_state.map_data["NPCs"].keys():
            return s.gm_NLG.talk_to_npc(npc="non_existing")

        elif npc not in game_state.map_data["locations"][game_state.player_pos]["NPCs"]:
            return s.gm_NLG.talk_to_npc(npc=npc, option="not_here")

        elif "talk" not in game_state.map_data["NPCs"][npc]["interactions"]:
            return s.gm_NLG.talk_to_npc(npc="not_possible")

        elif npc not in game_state.knowledge:
            game_state.talking_to = npc
            game_state.knowledge.append(npc)
            return s.gm_NLG.talk_to_npc(npc=npc, option="unknown") +\
                   f"\n\nYou are now talking with the {npc}. Just say goodbye to him when you want to talk with me again."

        else:
            game_state.talking_to = npc
            return s.gm_NLG.talk_to_npc(npc=npc, option="known") +\
                   f"\n\nYou are now talking with the {npc}. Remember to say goodbye to him when you want to talk with me again."

    # Only returns info about the current LOCATION. Not inventory nor health info
    def explore(s, game_state, params):
        if game_state.game_mode == "close":
            return f"You are at the {game_state.player_pos}\n" + s.tell_options(game_state)

        res = ""

        objects = game_state.map_data["locations"][game_state.player_pos]["objects"]
        if not objects: res += s.gm_NLG.explore(variant="objects", level="zero")
        elif len(objects) == 1: res += s.gm_NLG.explore(variant="objects", level="one", param1=objects[0])
        else:
            for idx, obj in enumerate(objects):
                if idx == 0: res += s.gm_NLG.explore(variant="objects", level="multiple", param1=obj)  # First object
                elif idx == len(objects)-1: res += f" and a {obj}. "  # Last object
                else: res += f", a {obj}"

        npcs = game_state.map_data["locations"][game_state.player_pos]["NPCs"]
        if not npcs: res += s.gm_NLG.explore(variant="npcs", level="zero")
        elif len(npcs) == 1: res += s.gm_NLG.explore(variant="npcs", level="one", param1=npcs[0], param2=game_state.map_data["NPCs"][npcs[0]]["interactions"][0])
        else:
            for idx, npc in enumerate(npcs):
                if idx == 0: res += s.gm_NLG.explore(variant="npcs", level="multiple", param1=npc, param2=game_state.map_data["NPCs"][npc]["interactions"][0])  # First npc
                elif idx == len(npcs)-1: res += f', or {game_state.map_data["NPCs"][npc]["interactions"][0]} with the {npc}. '  # Last npc
                else: res += f', {game_state.map_data["NPCs"][npc]["interactions"][0]} with the {npc}'

        links = game_state.map_data["locations"][game_state.player_pos]["links"]
        if not links: res += s.gm_NLG.explore(variant="links", level="zero")
        elif len(links) == 1: res += s.gm_NLG.explore(variant="links", level="one", param1=links[0])
        else:
            for idx, link in enumerate(links):
                if idx == 0: res += s.gm_NLG.explore(variant="links", level="multiple", param1=link)  # First link
                elif idx == len(links)-1: res += f", or the {link}."  # Last link
                else: res += f", the {link}"

        return res

    # Returns the player's location
    def get_position_info(s, game_state, params):
        res = s.gm_NLG.get_position_info(game_state.player_name, location=game_state.player_pos)
        return res

    # Returns info about what the player has in the INVENTORY
    def get_inventory_info(s, game_state, params):
        if not game_state.inventory:
            return s.gm_NLG.get_inventory_info(option="empty")

        if len(game_state.inventory) == 1:
            obj = f"an {game_state.inventory[0]}" if s.starts_with_vowel(game_state.inventory[0]) else f"a {game_state.inventory[0]}"
            action = game_state.map_data['objects'][game_state.inventory[0]]['action']
            return s.gm_NLG.get_inventory_info(option="one_element", obj=obj, action=action)
        else:
            res = s.gm_NLG.get_inventory_info(option="various_elements")

            current_action = ""
            for idx, obj in enumerate(game_state.inventory):
                new_action = game_state.map_data['objects'][obj]['action']
                if new_action == current_action: new_action = ""
                else:
                    current_action = new_action
                    new_action = " " + new_action

                if idx == 0: res += f"{new_action} an {obj}" if s.starts_with_vowel(obj) else f"{new_action} a {obj}"  # First object
                elif idx == len(game_state.inventory) - 1:
                    res += f" and{new_action} an {obj}." if s.starts_with_vowel(obj) else f" and{new_action} a {obj}"  # Last object
                else:
                    res += f",{new_action} an {obj}" if s.starts_with_vowel(obj) else f",{new_action} a {obj}"

            return res

    # Returns info about the player's HEALTH and ¿KNOWLEDGE?
    def get_player_info(s, game_state, params):
        health = game_state.map_data['player_info']['health']
        res = s.gm_NLG.get_player_info(game_state.player_name, health)
        return res

    # Basic functions / utils
    @staticmethod
    def load_map(game_state, map_filepath):
        if not os.path.isfile(map_filepath):
            colorPrint(f"FSM: Could not load map data file (file not found)", RED)
            return
        with open(map_filepath, 'r') as f:
            game_state.map_data = json.load(f)

        game_state.player_pos = game_state.map_data["start_position"]
        game_state.inventory = game_state.map_data["inventory"]
        game_state.knowledge = game_state.map_data["knowledge"]
        game_state.knowledge.append(game_state.player_pos)
        game_state.places_visited.append(game_state.player_pos)

        for npc in game_state.map_data["NPCs"].keys():
            game_state.emotion_score[npc] = game_state.map_data["NPCs"][npc]["attitude"]

    @staticmethod
    def starts_with_vowel(word):
        if word[0].lower() in ['a', 'e', 'i', 'o', 'u']:
            return True
        return False

    def start_game(s, game_state, option):
        game_state.game_type = option
        ########################### JUST GPT-2 ###########################
        if option == "gpt2":
            game_state.game_mode = option
            game_state.player_pos = "Spawn point"
            game_state.knowledge.append(game_state.player_pos)
            game_state.places_visited.append(game_state.player_pos)

            res, updated_map = s.gpt2.getGpt2Prediction(map_object=EMPTY_MAP_OBJECT,
                                                        come_from=None,
                                                        place_name=game_state.player_pos,
                                                        input_text="Welcome friend, let me guide you through this story. " + s.gm_NLG.gpt2_intro(location=game_state.player_pos))

            if res is None or res == "":
                return "GPT-2 server is not working. Try again later."

            game_state.map_data = updated_map
            return res
        ########################### JUST GPT-2 ###########################
        else:
            s.load_map(game_state, MAP_FILEPATH)
            game_state.game_mode = option
            if game_state.game_mode == "close":
                return s.gm_NLG.start_game() + "\n" + s.tell_options(game_state)

            return s.gm_NLG.start_game()

    def end_game(s, game_state, option):
        game_state.end_type = option
        game_state.is_over = True
        return s.gm_NLG.end_game(option=option) +\
               f"\n\nHey! Now that the game is over, please, take a minute to fill out our questionnaire:" \
                   f" https://forms.gle/ZUTdnzoHQ84gF3Rf9 \n\nYour ID is: {game_state.game_id}"

    @staticmethod
    def tell_options(game_state):
        if game_state.game_mode != "close":
            return ""

        options = ""

        options += "You can go to: \n"
        links = game_state.map_data["locations"][game_state.player_pos]["links"]
        for link in links:
            options += f"- The {link}\n"

        npcs = game_state.map_data["locations"][game_state.player_pos]["NPCs"]
        if any("talk" in game_state.map_data["NPCs"][npc]["interactions"] for npc in npcs):
            options += "You can talk to: \n"
            for npc in npcs:
                if "talk" in game_state.map_data["NPCs"][npc]["interactions"]:
                    options += f"- The {npc}\n"

        if any("fight" in game_state.map_data["NPCs"][npc]["interactions"] for npc in npcs):
            options += "You can attack to: \n"
            for npc in npcs:
                if "fight" in game_state.map_data["NPCs"][npc]["interactions"]:
                    options += f"- The {npc}\n"

        objects = game_state.map_data["locations"][game_state.player_pos]["objects"]
        if objects:
            options += "You can pick up: \n"
            for obj in objects:
                options += f"- The {obj}\n"

        return options
