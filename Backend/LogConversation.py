import datetime
from config import TIME_FORMAT
from DataFromLog import data_from_log


class Logger:
    def __init__(self, path):
        self.path = path
        self.game_id = ""
        self.user_message = ""
        self.rasa_confidence = {}
        self.bot_response = ""

    def log_game_id(self, game_id):
        self.game_id = game_id

    def log_user_message(self, user_message):
        self.user_message = user_message

    def log_rasa_confidence(self, rasa_confidence):
        self.rasa_confidence = rasa_confidence

    def log_bot_response(self, bot_response):
        self.bot_response = bot_response

    def log_flush(self):
        self.user_message = self.user_message.replace('\n', ' ')
        self.bot_response = self.bot_response.replace('\n', ' ')
        with open(self.path + "/game_" + self.game_id + ".tsv", "a+") as f:
            f.write(str(datetime.datetime.now().strftime(TIME_FORMAT))
                    + '\t' + self.user_message
                    + '\t' + (self.rasa_confidence["name"] if "name" in self.rasa_confidence else "")
                    + '\t' + (str(self.rasa_confidence["confidence"]) if "confidence" in self.rasa_confidence else "0.0")
                    + '\t' + self.bot_response
                    + '\n')
        self.game_id = ""
        self.user_message = ""
        self.rasa_confidence = {}
        self.bot_response = ""

    def log_new_game(self, user_id, game_id):

        with open(self.path + "/game_" + game_id + ".tsv", "w+") as f:
            f.write("time"
                    + '\t' + "user message"
                    + '\t' + "intent"
                    + '\t' + "confidence"
                    + '\t' + "bot response"
                    + '\n')

    def log_end_game(self, user_id, game_id, game_state):

        data = data_from_log(self.path + "/game_" + game_id + ".tsv")
        with open(self.path + "/user_" + user_id + ".tsv", "a+") as f:
            f.write(game_id
                    + '\t' + data["total_time"]
                    + '\t' + str(data["nb_turn"])
                    + '\t' + game_state.game_type
                    + '\t' + game_state.end_type
                    + '\t' + str(game_state.nb_turn_npc)
                    + '\t' + str(len(list(dict.fromkeys(game_state.places_visited))))
                    + '\n')
