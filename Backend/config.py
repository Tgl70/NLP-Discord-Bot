BOT_NAME = "toby"
FALLBACK_BOT_NAME = "boby"

SERVER_IP = "seblg.eu"
SERVER_PORT = 5130
FALLBACK_SERVER_PORT = 5140

# Will be used when rasa will be on seb's server
RASA_ADDRESS = "http://localhost:5005"

# Ngrok for dev
# RASA_ADDRESS = f"http://9a79788a.ngrok.io"  # Cesar

RASA_CHAT_ENDPOINT = f"{RASA_ADDRESS}/webhooks/rest/webhook"
RASA_NLU_ENDPOINT = f"{RASA_ADDRESS}/model/parse"


BOT_TO_ALANA_PAYLOAD = {
    'result': "",
    'bot_name': BOT_NAME,
    'bot_version': '1',
    # Flag to state that a bot is requesting to handle the next turn as well.
    'lock_requested': False,
    # the "helper attributes" that the bot requests to be saved
    # (will go in the "bot_state" of the state object)
    'bot_params': None,
    'user_attributes': {},
    'tts_emotion': '',
    'log_output': ''
}

# FSM
# MAP_FILEPATH = "./data/map.json"
MAP_FILEPATH = "/home/seb/project/f21ca-cw/Backend/data/map.json"

# GM_Responses
# GM_RESP_FILEPATH = "./data/GMResponses.json"
GM_RESP_FILEPATH = "/home/seb/project/f21ca-cw/Backend/data/GMResponses.json"

# NPCs_Responses
# NPC_RESP_FILEPATH = "./data/NPCsResponses.json"
NPC_RESP_FILEPATH = "/home/seb/project/f21ca-cw/Backend/data/NPCsResponses.json"

# LOG Folder
LOGS_FOLDERPATH = "/home/seb/project/f21ca-cw/Backend/logs"


TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

GPT2_ENDPOINT = "http://seblg.eu:6666"

IGNORE = -1
POSITION = 0
HEALTH = 1
PICKABLE = 2
FURNITURE = 3
INTERACTABLE = 4
LIGHT = 5

RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
GREY = "\x1b[90m"

RESET = "\x1b[0m"

CONV_DICT = {
     -1: "IGNORE",
     0: "POSITION",
     1: "HEALTH",
     2: "PICKABLE",
     3: "FURNITURE",
     4: "INTERACTABLE",
     5: "LIGHT"
}

TYPE_DICT = {
    # Position
    "geographical_area": POSITION,
    "location": POSITION,
    "area": POSITION,
    "village": POSITION,
    "small_town": POSITION,
    "settlement": POSITION,
    "room": POSITION,
    "building": POSITION,
    "way": POSITION,
    "structure": POSITION,
    "geological_formation": POSITION,

    # PU
    "food": HEALTH,
    # Item
    "object": PICKABLE,
    "physical_object": PICKABLE,
    "artifact": PICKABLE,
    "physical_entity": PICKABLE,
    "material": PICKABLE,
    # Furniture
    "furniture": FURNITURE,
    "piece_of_furniture": FURNITURE,

    # Interact
    "person": INTERACTABLE,
    "owner": INTERACTABLE,
    "people": INTERACTABLE,
    "social_group": INTERACTABLE,

    "vehicle": INTERACTABLE,
    "living_thing": INTERACTABLE,
    "animal": INTERACTABLE,
    # Light
    "source_of_illumination": LIGHT,
    "light": LIGHT,

    # Ignore
    "fluid": IGNORE,
    "abstraction": IGNORE,
    "body_covering": IGNORE,
    "body_part": IGNORE,
    "process": IGNORE
}

EXCLUDE_LIST = [
    "i",
    "me",
    "he",
    "you",
    "she",
    "it",
    "we",
    "us",
    "they"
]

EMPTY_MAP_OBJECT = {
        "start_position": "spawn point",
        "player_info": {
                "health_max": 20,
                "health": 20
        },
        "inventory": [],
        "knowledge": [],
        "locations": {},
        "objects": {},
        "NPCs": {}
}
