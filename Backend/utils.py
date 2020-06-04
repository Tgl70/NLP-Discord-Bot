import uuid

RED = "\x1b[31m"
YELLOW = "\x1b[33m"
GREEN = "\x1b[32m"
BLUE = "\x1b[36m"
RESET = "\x1b[0m"


def colorPrint(msg, color):
    print(color + msg + RESET)


class GameState:

    def __init__(self):
        self.game_id = str(uuid.uuid1())

        # Log
        self.game_type = ""
        self.end_type = "Unfinished"
        self.nb_turn_npc = 0
        self.places_visited = []

        # Domain
        self.map_data = {}

        self.game_mode = ""

        # State parameters
        self.history = []
        self.pending_action = ""
        self.player_pos = ""
        self.player_name = ""
        self.inventory = []
        self.knowledge = []

        self.talking_to = "Game_master"
        self.emotion_score = {}  # -1: Sad/Afraid/Negative | 1: Happy/Talkative/Positive
        self.misleading_turns = 0

        self.is_over = False
