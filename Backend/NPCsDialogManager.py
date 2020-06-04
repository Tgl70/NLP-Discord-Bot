#!/usr/bin/env python3
import json
import os.path
from config import *
from utils import *
import random


class NPCsDialogManager:

    def __init__(self):
        if not os.path.isfile(NPC_RESP_FILEPATH):
            colorPrint(f"NPCsDialogManager: Could not load NPCs responses data file (file not found)", RED)
            exit(1)

        with open(NPC_RESP_FILEPATH, 'r') as f:
            self.responses = json.load(f)

    def action(self, game_state, intent):
        npc = game_state.talking_to
        emotion_score = game_state.emotion_score[npc]  # -1 { Sad/Afraid/Negative } | 1 { Happy/Talkative/Positive }
        attitude = "pos" if emotion_score > 1 else "neg"

        # This will happen for intents such as move_to or attack, that ONLY apply to the game master
        if intent not in self.responses[npc].keys():
            if game_state.misleading_turns >= 3: return random.choice(self.responses[npc]["force_back"][attitude])
            else: return ""

        game_state.misleading_turns = 0
        return random.choice(self.responses[npc][intent][attitude])
